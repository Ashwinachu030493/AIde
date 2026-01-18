from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from server.shared.database import Base


class AuditRun(Base):
    """Tracks execution of a project audit"""

    """Tracks execution of a project audit"""
    __tablename__ = "audit_runs_persistent"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    project_id = Column(String(100), nullable=False)

    # Stats
    total_files = Column(Integer, default=0)
    files_with_issues = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)

    # Issues breakdown
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)

    health_score = Column(Integer, default=100)

    # Status
    # 'processing', 'completed', 'failed'
    status = Column(String(20), default="processing")
    error_message = Column(Text)

    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

    # Relationships
    findings = relationship("AuditFinding", back_populates="run", cascade="all, delete-orphan")


class AuditFinding(Base):
    """Individual violation found during audit"""

    """Individual violation found during audit"""
    __tablename__ = "audit_findings_persistent"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs_persistent.id"))
    project_id = Column(String(100), nullable=False)

    file_path = Column(Text, nullable=False)
    rule_id = Column(String(50), nullable=False)
    line_number = Column(Integer)
    column_number = Column(Integer)

    message = Column(Text, nullable=False)
    snippet = Column(Text)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info

    fix_suggestion = Column(Text)
    status = Column(String(20), default="open")  # open, fixed, ignored

    audit_metadata = Column(Text)  # JSON string for extra data

    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

    # Relationships
    run = relationship("AuditRun", back_populates="findings")
