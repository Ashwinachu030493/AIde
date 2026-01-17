import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

# Import engine and types
from server.auditor.scanning_engine import AuditEngine
from server.auditor.rules import AuditRule, Severity
from server.models.audit import AuditViolation  # Pydantic model

logger = logging.getLogger(__name__)

class PersistentAuditor(AuditEngine):
    """Auditor service that persists results to database"""
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def audit_project_persistent(self, project_id: str, project_path: str) -> Dict[str, Any]:
        """Audit project and persist results to database"""
        from server.models.auditor import AuditRun
        
        # Create audit run record
        audit_run = AuditRun(
            project_id=project_id,
            status='processing',
            started_at=datetime.utcnow()
        )
        self.db.add(audit_run)
        self.db.commit()
        
        try:
            # Get project files (simplified walk)
            import os
            from server.ingestion.parser import CodeParser
            parser = CodeParser()
            
            project_files = []
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if parser.should_parse_file(file_path):
                        try:
                            language = parser.detect_language(file_path)
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            project_files.append((file_path, content, language))
                        except:
                            continue
            
            audit_run.total_files = len(project_files)
            self.db.commit()
            
            # Audit each file
            all_violations: List[AuditViolation] = []
            files_with_issues = 0
            
            for i, (file_path, content, language) in enumerate(project_files, 1):
                try:
                    result = self.scan_file(content, file_path, language)
                    if result.violations:
                        all_violations.extend(result.violations)
                        files_with_issues += 1
                        
                        # Persist findings
                        for violation in result.violations:
                            self._persist_finding(audit_run.id, project_id, violation)
                    
                    # Update progress occasionally
                    if i % 10 == 0:
                        self.db.refresh(audit_run) # Keep alive
                        
                except Exception as e:
                    logger.error(f"Failed to audit {file_path}: {e}")
            
            # Update audit run with aggregate stats
            severity_counts = self._count_issues_by_severity(all_violations)
            health_score = self._calculate_health_score(all_violations, len(project_files))
            
            audit_run.status = 'completed'
            audit_run.files_with_issues = files_with_issues
            audit_run.total_issues = len(all_violations)
            
            # Map severities (Pydantic enum might need string conversion)
            audit_run.critical_issues = severity_counts.get("critical", 0)
            audit_run.high_issues = severity_counts.get("high", 0) # Mapping needed if enum distinct
            # Our Severity enum has CRITICAL, WARNING, INFO.
            # Let's map loosely:
            # CRITICAL -> critical
            # WARNING -> high (or medium? let's say medium to match schema)
            # INFO -> low
            
            audit_run.critical_issues = severity_counts.get(Severity.CRITICAL, 0)
            audit_run.medium_issues = severity_counts.get(Severity.WARNING, 0)
            audit_run.low_issues = severity_counts.get(Severity.INFO, 0)
            
            audit_run.health_score = health_score
            audit_run.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                'audit_run_id': audit_run.id,
                'project_id': project_id,
                'total_files': len(project_files),
                'files_with_issues': files_with_issues,
                'total_issues': len(all_violations),
                'health_score': health_score,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Project audit failed: {e}")
            audit_run.status = 'failed'
            audit_run.error_message = str(e)
            audit_run.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _persist_finding(self, audit_run_id: int, project_id: str, violation: AuditViolation):
        """Persist a single audit finding to database"""
        from server.models.auditor import AuditFinding
        
        # Logic to extract snippets if not in violation?
        # Violation has line_content but not full snippet.
        
        finding = AuditFinding(
            audit_run_id=audit_run_id,
            project_id=project_id,
            file_path=violation.file_path,
            rule_id=violation.rule_id,
            line_number=violation.line_number,
            message=violation.description, # Mapping description to message
            snippet=violation.line_content,
            severity=violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
            fix_suggestion=None, # Not currently generated
            status='open',
            audit_metadata=None # Was metadata
        )
        
        self.db.add(finding)
    
    def _count_issues_by_severity(self, violations: List[AuditViolation]) -> Dict[str, int]:
        """Count issues by severity"""
        counts = {}
        for v in violations:
            s = v.severity
            counts[s] = counts.get(s, 0) + 1
        return counts
    
    def _calculate_health_score(self, violations: List[AuditViolation], total_files: int) -> int:
        """Calculate project health score (0-100)"""
        if total_files == 0:
            return 100
        
        # Penalties per issue
        penalty_map = {
            Severity.CRITICAL: 10,
            Severity.WARNING: 3,
            Severity.INFO: 0.5
        }
        
        total_penalty = 0
        for v in violations:
            total_penalty += penalty_map.get(v.severity, 1)
        
        # Namespace penalty to file count to avoid negative scaling on large repos
        # A project with many files can handle more issues? 
        # Metric: Penalties per file
        avg_penalty_per_file = total_penalty / total_files
        
        # If avg_penalty_per_file is 0, score 100.
        # If avg_penalty_per_file is 10 (e.g. 1 critical per file), score 0.
        
        score = 100 - (avg_penalty_per_file * 10)
        return int(max(0, min(100, score)))
