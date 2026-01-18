import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import case, desc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FileIndexTracker:
    """Track file indexing status in database"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def update_file_status(
        self,
        project_id: str,
        file_path: str,
        status: str,
        chunks_count: int = 0,
        error_message: Optional[str] = None,
    ):
        """Update or create file index status"""
        from server.models.file_index import FileIndexStatus

        # Calculate file hash to detect changes
        file_hash = self._calculate_file_hash(file_path) or "unknown"

        # Check if record exists
        record = (
            self.db.query(FileIndexStatus)
            .filter_by(project_id=project_id, file_path=file_path)
            .first()
        )

        if record:
            # Update existing
            record.file_hash = file_hash
            record.status = status
            record.chunks_count = chunks_count
            record.error_message = error_message
            if status == "indexed":
                record.indexed_at = datetime.utcnow()
        else:
            # Create new
            record = FileIndexStatus(
                project_id=project_id,
                file_path=file_path,
                file_hash=file_hash,
                status=status,
                chunks_count=chunks_count,
                error_message=error_message,
            )
            if status == "indexed":
                record.indexed_at = datetime.utcnow()
            self.db.add(record)

        self.db.commit()

    def get_project_stats(self, project_id: str) -> Dict:
        """Get indexing statistics for project"""
        from sqlalchemy import func

        from server.models.file_index import FileIndexStatus

        # Using a safer way to query aggregate
        total = (
            self.db.query(func.count(FileIndexStatus.id)).filter_by(project_id=project_id).scalar()
            or 0
        )
        indexed = (
            self.db.query(func.count(FileIndexStatus.id))
            .filter_by(project_id=project_id, status="indexed")
            .scalar()
            or 0
        )
        errors = (
            self.db.query(func.count(FileIndexStatus.id))
            .filter_by(project_id=project_id, status="error")
            .scalar()
            or 0
        )
        chunks = (
            self.db.query(func.sum(FileIndexStatus.chunks_count))
            .filter_by(project_id=project_id)
            .scalar()
            or 0
        )

        return {
            "total_files": total,
            "indexed_files": indexed,
            "error_files": errors,
            "total_chunks": chunks,
        }

    def get_recently_indexed(self, project_id: str, limit: int = 10) -> List[Dict]:
        """Get recently indexed files"""
        from server.models.file_index import FileIndexStatus

        files = (
            self.db.query(FileIndexStatus)
            .filter_by(project_id=project_id, status="indexed")
            .order_by(FileIndexStatus.indexed_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "file_path": f.file_path,
                "chunks_count": f.chunks_count,
                "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
            }
            for f in files
        ]

    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of file content"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
