import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from server.auditor.service_persistent import PersistentAuditor
from server.models.auditor import AuditFinding, AuditRun
from server.shared.database import get_db

router = APIRouter(prefix="/auditor", tags=["auditor"])
logger = logging.getLogger(__name__)


async def run_persistent_audit(auditor: PersistentAuditor, project_id: str, project_path: str):
    """Background task for persistent audit"""
    try:
        result = auditor.audit_project_persistent(project_id, project_path)
        logger.info(
            f"Persistent audit completed: {project_id}. Score: {result.get('health_score')}"
        )
    except Exception as e:
        logger.error(f"Persistent audit failed: {e}")


@router.post("/project/{project_id}/persistent")
async def audit_project_persistent(
    project_id: str,
    project_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Audit project with persistent results"""

    try:
        auditor = PersistentAuditor(db)

        # Start background audit
        background_tasks.add_task(
            run_persistent_audit, auditor=auditor, project_id=project_id, project_path=project_path
        )

        return JSONResponse(
            {
                "status": "started",
                "project_id": project_id,
                "message": "Audit started with persistence",
            }
        )

    except Exception as e:
        logger.error(f"Failed to start persistent audit: {e}")
        raise HTTPException(500, f"Failed to start audit: {str(e)}")


@router.get("/project/{project_id}/runs")
async def get_audit_runs(
    project_id: str, limit: int = 10, db: Session = Depends(get_db)
) -> JSONResponse:
    """Get audit run history for a project"""

    try:
        runs = (
            db.query(AuditRun)
            .filter_by(project_id=project_id)
            .order_by(desc(AuditRun.started_at))
            .limit(limit)
            .all()
        )

        return JSONResponse(
            {
                "project_id": project_id,
                "total_runs": len(runs),
                "runs": [
                    {
                        "id": run.id,
                        "status": run.status,
                        "total_files": run.total_files,
                        "files_with_issues": run.files_with_issues,
                        "total_issues": run.total_issues,
                        "critical_issues": run.critical_issues,
                        "high_issues": run.high_issues,
                        "medium_issues": run.medium_issues,
                        "low_issues": run.low_issues,
                        "health_score": run.health_score,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "error_message": run.error_message,
                    }
                    for run in runs
                ],
            }
        )

    except Exception as e:
        logger.error(f"Failed to get audit runs: {e}")
        raise HTTPException(500, f"Failed to get audit runs: {str(e)}")


@router.get("/project/{project_id}/findings")
async def get_project_findings(
    project_id: str,
    severity: Optional[str] = None,
    status: Optional[str] = "open",
    limit: int = 100,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get audit findings for a project"""

    try:
        query = db.query(AuditFinding).filter_by(
            project_id=project_id,
        )

        if status:
            query = query.filter_by(status=status)

        if severity:
            query = query.filter_by(severity=severity)

        findings = (
            query.order_by(desc(AuditFinding.severity), desc(AuditFinding.created_at))
            .limit(limit)
            .all()
        )

        return JSONResponse(
            {
                "project_id": project_id,
                "total_findings": len(findings),
                "findings": [
                    {
                        "id": finding.id,
                        "audit_run_id": finding.audit_run_id,
                        "file_path": finding.file_path,
                        "rule_id": finding.rule_id,
                        "line": finding.line_number,
                        "message": finding.message,
                        "severity": finding.severity,
                        "status": finding.status,
                        "snippet": finding.snippet,
                        "fix": finding.fix_suggestion,
                        "created_at": (
                            finding.created_at.isoformat() if finding.created_at else None
                        ),
                        "resolved_at": (
                            finding.resolved_at.isoformat() if finding.resolved_at else None
                        ),
                    }
                    for finding in findings
                ],
            }
        )

    except Exception as e:
        logger.error(f"Failed to get findings: {e}")
        raise HTTPException(500, f"Failed to get findings: {str(e)}")
