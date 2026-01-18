import logging
from datetime import datetime
from typing import List

from server.auditor.rules import ALL_RULES, AuditRule
from server.models.audit import AuditResult, AuditViolation

logger = logging.getLogger(__name__)


class AuditEngine:
    """Stateless audit engine reused by persistent auditor."""

    def __init__(self):
        self.rules = ALL_RULES

    def scan_file(self, content: str, file_path: str, language: str = None) -> AuditResult:
        violations = []

        lines = content.split("\n")

        for rule in self.rules:
            # Only apply language-specific rules when language is known
            if language and rule.languages and language not in rule.languages:
                continue

            if rule.pattern:
                for i, line in enumerate(lines):
                    if rule.pattern.search(line):
                        violations.append(
                            AuditViolation(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                description=rule.description,
                                severity=rule.severity.value,
                                file_path=file_path,
                                line_number=i + 1,
                                line_content=line.strip(),
                            )
                        )

        return AuditResult(
            file_path=file_path,
            scan_timestamp=datetime.now().isoformat(),
            violations=violations,
        )

    def scan_project(self, project_path: str):
        # Placeholder; persistent auditor handles walking.
        pass
