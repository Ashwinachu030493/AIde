from typing import List
import re
from enum import Enum


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditRule:
    def __init__(self, id: str, name: str, description: str, severity: Severity, pattern: str = None, languages: List[str] = None):
        self.id = id
        self.name = name
        self.description = description
        self.severity = severity
        self.pattern = re.compile(pattern, re.MULTILINE | re.IGNORECASE) if pattern else None
        self.languages = languages or []


# Common security patterns (simplified for local/lite version)
SECURITY_RULES = [
    AuditRule(
        id="SEC001",
        name="Hardcoded API Key",
        description="Potential hardcoded API key or token detected",
        severity=Severity.CRITICAL,
        pattern=r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
        languages=["python", "javascript", "typescript", "java", "go"],
    ),
    AuditRule(
        id="SEC002",
        name="Insecure HTTP",
        description="Usage of insecure HTTP protocol",
        severity=Severity.WARNING,
        pattern=r"http://",
        languages=["python", "javascript", "typescript", "java", "go", "html"],
    ),
    AuditRule(
        id="SEC003",
        name="SQL Injection Risk",
        description="Potential string formatting in SQL query",
        severity=Severity.CRITICAL,
        pattern=r"(?i)(execute|cursor)\s*\(\s*f['\"]|format\s*\(",
        languages=["python"],
    ),
]


# Best practice patterns
QUALITY_RULES = [
    AuditRule(
        id="QUAL001",
        name="TODO/FIXME Comment",
        description="Leftover TODO or FIXME comment",
        severity=Severity.INFO,
        pattern=r"(?i)(TODO|FIXME):",
        languages=["python", "javascript", "typescript", "java", "cpp", "c"],
    ),
    AuditRule(
        id="QUAL002",
        name="Print Statement",
        description="Usage of print() instead of logging",
        severity=Severity.INFO,
        pattern=r"print\s*\(",
        languages=["python"],
    ),
    AuditRule(
        id="QUAL003",
        name="Console Log",
        description="Usage of console.log for debugging",
        severity=Severity.INFO,
        pattern=r"console\.log\s*\(",
        languages=["javascript", "typescript"],
    ),
]


ALL_RULES = SECURITY_RULES + QUALITY_RULES