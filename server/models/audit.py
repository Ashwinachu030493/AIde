from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AuditViolation(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    severity: Severity
    file_path: str
    line_number: int
    line_content: str
    
class AuditResult(BaseModel):
    file_path: str
    scan_timestamp: str
    violations: List[AuditViolation]
    error: Optional[str] = None
    
class ProjectAuditSummary(BaseModel):
    total_files: int
    files_with_issues: int
    total_violations: int
    critical_count: int
    warning_count: int
    info_count: int
