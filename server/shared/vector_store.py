import asyncio
import hashlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB wrapper with async support and project-specific collections"""

    def __init__(self):
        self.host = os.getenv("CHROMA_SERVER_HOST", "local")

        if self.host == "local":
            self.client = chromadb.PersistentClient(path="./chroma_data")
        else:
            self.client = chromadb.HttpClient(
                host=self.host,
                settings=Settings(chroma_server_ssl_enabled=False, anonymized_telemetry=False),
            )

        self.embedding_fn = self._init_embedding_function()

    def _init_embedding_function(self):
        """Initialize embedding function with timeout and offline-friendly fallback."""
        offline_flag = os.getenv("TRANSFORMERS_OFFLINE", "0") == "1"
        explicit_path = os.getenv("EMBEDDING_MODEL_PATH")
        explicit_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

        # Choose model source: prefer explicit path if it exists, else explicit name, else default.
        model_target = explicit_name
        if explicit_path:
            if os.path.exists(explicit_path):
                model_target = explicit_path
            else:
                logger.warning(
                    "EMBEDDING_MODEL_PATH is set but does not exist; falling back to model name."
                )

        # If explicitly offline and no usable local path, skip expensive load entirely.
        if offline_flag and (not explicit_path or not os.path.exists(explicit_path)):
            logger.info("TRANSFORMERS_OFFLINE=1 with no local model; using dummy embeddings.")
            return self._dummy_embedding_fn()

        def build_embedding():
            return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_target)

        executor: Optional[ThreadPoolExecutor] = None
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(build_embedding)
            # Time-box initialization to avoid blocking startup on downloads.
            return future.result(timeout=5)
        except TimeoutError:
            logger.warning("Timed out loading SentenceTransformer (5s). Using dummy embeddings.")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}. Using dummy embeddings.")
        finally:
            if executor:
                executor.shutdown(wait=False)

        return self._dummy_embedding_fn()

    def _dummy_embedding_fn(self):
        """Return a cheap, deterministic dummy embedding function."""

        class DummyEmbeddingFunction:
            def __call__(self, input: List[str]) -> List[List[float]]:
                return [[0.0] * 384 for _ in input]

            def embed_query(self, input: str) -> List[List[float]]:
                """Embed a single query text (ChromaDB expects nested list)."""
                return [[0.0] * 384]

            def name(self) -> str:
                """Return name for ChromaDB compatibility."""
                return "DummyEmbedding"

        return DummyEmbeddingFunction()

    def _get_project_collection(self, project_id: str) -> chromadb.Collection:
        """Get or create collection for a project (Synchronous)"""
        collection_name = f"project_{project_id}"
        try:
            return self.client.get_collection(
                name=collection_name, embedding_function=self.embedding_fn
            )
        except:
            return self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,
                metadata={"project_id": project_id},
            )

    def _add_code_snippet_sync(
        self, project_id: str, code: str, file_path: str, function_name: Optional[str] = None
    ) -> str:
        """Add code snippet sync"""
        collection = self._get_project_collection(project_id)

        metadata = {
            "type": "code_snippet",
            "file_path": file_path,
            "function_name": function_name or "",
            "language": self._detect_language(file_path),
        }

        doc_id = hashlib.md5(f"{project_id}:{file_path}:{code}".encode()).hexdigest()

        collection.add(documents=[code], metadatas=[metadata], ids=[doc_id])
        return doc_id

    async def add_code_snippet(
        self, project_id: str, code: str, file_path: str, function_name: Optional[str] = None
    ) -> str:
        """Add code snippet async wrapper"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self._add_code_snippet_sync(project_id, code, file_path, function_name)
        )

    def _query_similar_code_sync(
        self, project_id: str, query: str, n_results: int = 5
    ) -> List[Dict]:
        """Query similar code sync"""
        collection = self._get_project_collection(project_id)

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results["documents"]:
            for doc, metadata, distance in zip(
                results["documents"][0], results["metadatas"][0], results["distances"][0]
            ):
                formatted_results.append(
                    {"content": doc, "metadata": metadata, "similarity": 1 - distance}
                )
        return formatted_results

    async def query_similar_code(
        self, project_id: str, query: str, n_results: int = 5
    ) -> List[Dict]:
        """Query similar code async wrapper - prevents event loop blocking"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self._query_similar_code_sync(project_id, query, n_results)
        )

    def _detect_language(self, file_path: str) -> str:
        """Simple language detection"""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".json": "json",
        }
        return mapping.get(ext, "unknown")
