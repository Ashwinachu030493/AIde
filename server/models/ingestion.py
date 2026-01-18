from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJob(BaseModel):
    """Represents an ingestion job state"""

    id: str
    project_id: str
    project_path: str
    status: IngestionStatus = IngestionStatus.PENDING

    # Progress
    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0

    # Statistics
    parser_stats: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.started_at:
            self.started_at = datetime.now()


class FileIngestionRequest(BaseModel):
    content: str
    file_path: str
    project_id: str
    language: Optional[str] = None


class ProjectIngestionRequest(BaseModel):
    project_path: str
    project_id: str
    max_workers: int = 4
