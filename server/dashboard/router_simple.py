from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, case

from server.shared.database import get_db
from server.services.file_index_tracker import FileIndexTracker

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

@router.get("/project/{project_id}/overview")
async def get_project_overview(
    project_id: str,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get comprehensive project overview for dashboard (polling endpoint)"""
    
    try:
        # 1. File Indexing Stats
        index_tracker = FileIndexTracker(db)
        index_stats = index_tracker.get_project_stats(project_id)
        
        # 2. LLM Usage Stats
        llm_stats = await _get_llm_usage_stats(project_id, db)
        
        # 3. Audit Stats
        audit_stats = await _get_audit_stats(project_id, db)
        
        # 4. Recent Activity
        recent_activity = await _get_recent_activity(project_id, db)
        
        # 5. Calculate Health Score
        health_score = _calculate_health_score(audit_stats, index_stats)
        
        return JSONResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "health": {
                "score": health_score,
                "breakdown": {
                    "code_quality": audit_stats.get('health_score', 100),
                    "coverage": _calculate_coverage_score(index_stats),
                    "freshness": _calculate_freshness_score(index_stats)
                }
            },
            "ingestion": index_stats,
            "audit": audit_stats,
            "usage": llm_stats,
            "activity": recent_activity,
            "quick_actions": _get_quick_actions(project_id, index_stats, audit_stats)
        })
        
    except Exception as e:
        logger.error(f"Dashboard overview failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to load dashboard: {str(e)}")

async def _get_llm_usage_stats(project_id: str, db: Session) -> Dict:
    """Get LLM usage statistics"""
    from server.models.llm_usage import LLMUsageLog
    
    # Today's usage
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Check if we have logs table (migration might depend on restart if using some ORMs, but here we query direct)
    
    today_stats = db.query(
        func.sum(LLMUsageLog.total_tokens).label('tokens_today'),
        func.sum(LLMUsageLog.estimated_cost_usd).label('cost_today'),
        func.count(LLMUsageLog.id).label('requests_today')
    ).filter(
        and_(
            LLMUsageLog.project_id.contains(project_id),  # Safe: SQLAlchemy parameterizes this
            LLMUsageLog.timestamp >= today_start
        )
    ).first()
    
    # Total usage
    total_stats = db.query(
        func.sum(LLMUsageLog.total_tokens).label('total_tokens'),
        func.sum(LLMUsageLog.estimated_cost_usd).label('total_cost'),
        func.count(LLMUsageLog.id).label('total_requests')
    ).filter(LLMUsageLog.project_id.contains(project_id)).first()
    
    return {
        "today": {
            "tokens": today_stats.tokens_today or 0,
            "cost_usd": float(round(today_stats.cost_today or 0, 4)),
            "requests": today_stats.requests_today or 0
        },
        "total": {
            "tokens": total_stats.total_tokens or 0,
            "cost_usd": float(round(total_stats.total_cost or 0, 4)),
            "requests": total_stats.total_requests or 0
        }
    }

async def _get_audit_stats(project_id: str, db: Session) -> Dict:
    """Get audit statistics"""
    from server.models.auditor import AuditRun, AuditFinding
    
    # Latest audit run
    latest_run = db.query(AuditRun).filter_by(
        project_id=project_id,
        status='completed'
    ).order_by(desc(AuditRun.completed_at)).first()
    
    if not latest_run:
        return {
            "last_run": None,
            "total_issues": 0,
            "critical_issues": 0,
            "health_score": 100,
            "open_issues": 0
        }
    
    # Open issues (approximation: finding connected to latest run)
    # Ideally should be stateful findings, but for now using latest run stats
    
    return {
        "last_run": latest_run.completed_at.isoformat() if latest_run.completed_at else None,
        "total_issues": latest_run.total_issues,
        "critical_issues": latest_run.critical_issues,
        "health_score": latest_run.health_score,
        "open_issues": latest_run.total_issues # Assuming all issues in last run are 'open'
    }

async def _get_recent_activity(project_id: str, db: Session) -> List[Dict]:
    """Get recent activity timeline"""
    activities = []
    
    # Recent LLM usage
    from server.models.llm_usage import LLMUsageLog
    recent_llm = db.query(LLMUsageLog).filter(
        LLMUsageLog.project_id.contains(project_id)
    ).order_by(desc(LLMUsageLog.timestamp)).limit(5).all()
    
    for usage in recent_llm:
        activities.append({
            "type": "llm_usage",
            "timestamp": usage.timestamp.isoformat(),
            "description": f"Used {usage.model}",
            "details": f"{usage.total_tokens} tokens"
        })
    
    # Recent audits
    from server.models.auditor import AuditRun
    recent_audits = db.query(AuditRun).filter_by(
        project_id=project_id
    ).order_by(desc(AuditRun.completed_at)).limit(3).all()
    
    for audit in recent_audits:
        if audit.completed_at:
            activities.append({
                "type": "audit",
                "timestamp": audit.completed_at.isoformat(),
                "description": "Audit completed",
                "details": f"Score: {audit.health_score}"
            })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:10]

def _calculate_health_score(audit_stats: Dict, index_stats: Dict) -> int:
    """Calculate overall health score (0-100)"""
    # Weighted average of components
    weights = {
        'code_quality': 0.6,  # Audit health score
        'coverage': 0.3,      # File indexing coverage
        'freshness': 0.1      # Data freshness
    }
    
    code_quality = audit_stats.get('health_score', 100)
    coverage = _calculate_coverage_score(index_stats)
    freshness = _calculate_freshness_score(index_stats)
    
    score = (
        code_quality * weights['code_quality'] +
        coverage * weights['coverage'] +
        freshness * weights['freshness']
    )
    
    return int(score)

def _calculate_coverage_score(index_stats: Dict) -> int:
    """Calculate file coverage score"""
    total = index_stats.get('total_files', 0)
    indexed = index_stats.get('indexed_files', 0)
    
    if total == 0:
        return 0 # No files means 0 coverage technically, or 100 if empty project? Let's say 0 to encourage ingestion.
    
    coverage = (indexed / total) * 100
    return int(min(coverage, 100))

def _calculate_freshness_score(index_stats: Dict) -> int:
    """Calculate data freshness score"""
    # Simplified: if we have any indexed files, consider it fresh
    if index_stats.get('indexed_files', 0) > 0:
        return 100
    return 0

def _get_quick_actions(project_id: str, index_stats: Dict, audit_stats: Dict) -> List[Dict]:
    """Get suggested quick actions based on current state"""
    actions = []
    
    # Check if indexing needed
    total_files = index_stats.get('total_files', 0)
    indexed_files = index_stats.get('indexed_files', 0)
    
    if indexed_files < total_files or total_files == 0:
        actions.append({
            "id": "ingest_project",
            "label": "Index Files",
            "description": f"{max(0, total_files - indexed_files)} unindexed files",
            "command": "aide.ingestProject"
        })
    
    # Check if audit needed
    last_audit = audit_stats.get('last_run')
    if not last_audit:
        actions.append({
            "id": "run_audit",
            "label": "Run Audit",
            "description": "No audit results found",
            "command": "aide.runAudit"
        })
    
    # Always available
    actions.append({
        "id": "open_chat",
        "label": "Ask AI",
        "description": "Get help with your code",
        "command": "aide.openChat"
    })
    
    return actions
