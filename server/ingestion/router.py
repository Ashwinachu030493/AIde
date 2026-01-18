import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from server.ingestion.parser import CodeChunk, CodeParser, FileMetadata
from server.models.ingestion import IngestionJob, IngestionStatus
from server.services.file_index_tracker import FileIndexTracker
from server.shared.database import get_db
from server.shared.vector_store import VectorStore

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
logger = logging.getLogger(__name__)

parser = CodeParser()
_vector_store: Optional[VectorStore] = None
ingestion_jobs: Dict[str, IngestionJob] = {}


def get_vector_store() -> VectorStore:
    """Lazy initialization of VectorStore to avoid blocking server startup"""
    global _vector_store
    if _vector_store is None:
        logger.info("Initializing VectorStore (lazy load)...")
        _vector_store = VectorStore()
        logger.info("✅ VectorStore initialized")
    return _vector_store


# Global executor for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)


@router.get("/capabilities")
async def get_capabilities():
    """Get parser capabilities for client info"""
    return {
        "supported_modes": [m.value for m in parser.capabilities.supported_modes],
        "tree_sitter_available": parser.capabilities.tree_sitter_available,
    }


async def ingest_project_background(
    job_id: str, project_path: str, project_id: str, max_workers: int, db: Session
):
    job = ingestion_jobs.get(job_id)
    if not job:
        return

    try:
        job.status = IngestionStatus.PROCESSING
        loop = asyncio.get_event_loop()

        # Initialize tracker
        tracker = FileIndexTracker(db)

        # 1. Scan (CPU bound)
        # Note: scan_project is synchronous in parser, so run in executor
        scan_results = await loop.run_in_executor(executor, parser.scan_project, project_path)
        job.total_files = len(scan_results)

        # 2. Process batches
        batch_size = 10
        for i in range(0, len(scan_results), batch_size):
            batch = scan_results[i : i + batch_size]

            # Process batch concurrently
            futures = []
            for item in batch:
                # item is (metadata, chunks, errors)
                futures.append(
                    loop.run_in_executor(executor, process_single_file_sync, item, project_id)
                )

            results = await asyncio.gather(*futures)

            # Update stats
            for res_meta, res_chunks, res_errors in results:
                job.processed_files += 1
                if res_errors or (res_meta and res_meta.error_messages):
                    job.failed_files += 1
                    errs = res_errors + (res_meta.error_messages if res_meta else [])
                    job.errors.extend(errs)
                else:
                    job.successful_files += 1
                    job.total_chunks += len(res_chunks)
                    if res_meta:
                        mode = res_meta.parser_mode_used.value
                        job.parser_stats[mode] = job.parser_stats.get(mode, 0) + 1

                        # Store in vector store (I/O bound-ish, but Chroma local is sync/blocking often,
                        # so keeping it in executor or doing here?
                        # VectorStore.add_code_snippet is async in our impl?
                        # Checking code: vector_store defines 'async def add_code_snippet' which runs 'run_in_executor'.
                        # So we should call it here in the loop, awaiting it.
                        # Wait, 'process_single_file_sync' assumes we do CPU work.
                        # We need to separate parsing (CPU) from Storing (I/O).
                        # Let's adjust logic:
                        # scan_project already parsed everything? Yes, scan_project calls parse_file.
                        # So scan_results already has chunks!
                        # We just need to store them.
                        # Storing is I/O. We can do it directly here using await.
                        pass

            # Actually store the batch
            # scan_project DOES parse, so we already have chunks.
            # We just need to iterate and store.
            vector_store = get_vector_store()  # Lazy init on first use
            for meta, chunks, errs in batch:
                if not meta:
                    continue  # Failed scan
                for chunk in chunks:
                    await vector_store.add_code_snippet(
                        project_id=project_id,
                        code=chunk.content,
                        file_path=meta.file_path,
                        function_name=chunk.metadata.get("element_name"),
                    )

            # Update status for each file in batch
            for meta, chunks, errs in batch:
                if not meta:
                    continue

                status = "error" if errs or meta.error_messages else "indexed"
                error_msg = "; ".join(errs + meta.error_messages) if status == "error" else None

                tracker.update_file_status(
                    project_id=project_id,
                    file_path=meta.file_path,
                    status=status,
                    chunks_count=len(chunks),
                    error_message=error_msg,
                )

        job.status = IngestionStatus.COMPLETED
        job.completed_at = datetime.now()

    except Exception as e:
        logger.error(f"Background ingestion failed: {e}")
        job.status = IngestionStatus.FAILED
        job.errors.append(str(e))
        job.completed_at = datetime.now()


def process_single_file_sync(item, project_id):
    # This helper is seemingly redundant if scan_project parses everything.
    # scan_project in parser.py calls parse_file.
    # So we don't need to re-parse.
    # Just passing through for structure if needed, but returning item as is.
    return item


@router.post("/project")
async def ingest_project(
    background_tasks: BackgroundTasks,
    project_path: str = Form(...),
    project_id: str = Form(...),
    max_workers: int = Form(4),
    db: Session = Depends(get_db),
):
    # Resize executor if needed
    global executor
    if executor._max_workers != max_workers:
        executor = ThreadPoolExecutor(max_workers=max_workers)

    job_id = f"job_{project_id}_{int(asyncio.get_event_loop().time())}"
    job = IngestionJob(id=job_id, project_id=project_id, project_path=project_path)
    ingestion_jobs[job_id] = job

    background_tasks.add_task(
        ingest_project_background,
        job_id=job_id,
        project_path=project_path,
        project_id=project_id,
        max_workers=max_workers,
        db=db,
    )

    return JSONResponse(
        {
            "status": "started",
            "job_id": job_id,
            "capabilities": {
                "tree_sitter": parser.capabilities.tree_sitter_available,
                "modes": [m.value for m in parser.capabilities.supported_modes],
            },
        }
    )


@router.post("/file")
async def ingest_file(
    content: str = Form(...),
    file_path: str = Form(...),
    project_id: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        loop = asyncio.get_event_loop()
        # Parse in thread
        metadata, chunks = await loop.run_in_executor(
            executor, parser.parse_file, file_path, content
        )

        # Store
        vector_store = get_vector_store()  # Lazy init on first use
        for chunk in chunks:
            await vector_store.add_code_snippet(
                project_id, chunk.content, file_path, chunk.metadata.get("element_name")
            )

        # Track status
        tracker = FileIndexTracker(db)
        status = "error" if metadata.error_messages else "indexed"
        error_msg = "; ".join(metadata.error_messages) if metadata.error_messages else None

        tracker.update_file_status(
            project_id=project_id,
            file_path=file_path,
            status=status,
            chunks_count=len(chunks),
            error_message=error_msg,
        )

        return JSONResponse(
            {
                "status": "success",
                "chunks": len(chunks),
                "mode": metadata.parser_mode_used.value,
                "errors": metadata.error_messages,
            }
        )
    except Exception as e:
        logger.error(f"Ingest file error: {e}")
        raise HTTPException(500, str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    job = ingestion_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
