from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from server.shared.database import Base

class FileIndexStatus(Base):
    __tablename__ = 'file_index_status'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    project_id = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False)  # indexed, pending, error
    
    chunks_count = Column(Integer, default=0)
    indexed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
