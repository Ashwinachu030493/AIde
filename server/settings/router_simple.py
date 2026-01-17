from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from sqlalchemy.orm import Session

from server.services.encryption_simple import SimpleEncryption
from server.shared.database import get_db
from server.models.user_simple import UserSettings, APIKeyUsage

router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)

encryption = SimpleEncryption()

class APIKeyUpdate(BaseModel):
    provider: str
    api_key: Optional[str] = None

class UserPreferences(BaseModel):
    default_model: Optional[str] = None
    theme: Optional[str] = None
    auto_ingest: Optional[bool] = None
    max_file_size_mb: Optional[int] = None

@router.get("/")
async def get_settings(db: Session = Depends(get_db)):
    """Get current settings (API keys are never returned decrypted)"""
    settings = db.query(UserSettings).filter_by(is_active=1).first()
    
    if not settings:
        return {"has_settings": False}
    
    providers = {}
    for p in ['openai', 'anthropic', 'groq', 'huggingface', 'github']:
        key_exists = getattr(settings, f"{p}_api_key")
        providers[p] = bool(key_exists)
            
    return {
        "has_settings": True,
        "preferences": {
            "default_model": settings.default_model,
            "theme": settings.theme,
            "auto_ingest": bool(settings.auto_ingest),
            "max_file_size_mb": settings.max_file_size_mb
        },
        "providers_configured": providers
    }

@router.post("/api-keys")
async def update_api_key(update: APIKeyUpdate, db: Session = Depends(get_db)):
    valid_providers = ['openai', 'anthropic', 'groq', 'huggingface', 'github']
    if update.provider not in valid_providers:
        raise HTTPException(400, "Invalid provider")
        
    if update.api_key and not encryption.validate_api_key(update.provider, update.api_key):
        raise HTTPException(400, "Invalid API key format")
        
    settings = db.query(UserSettings).filter_by(is_active=1).first()
    if not settings:
        settings = UserSettings(is_active=1)
        db.add(settings)
        
    field = f"{update.provider}_api_key"
    if update.api_key is None:
        setattr(settings, field, None)
        action = "removed"
    else:
        encrypted = encryption.encrypt(update.api_key)
        setattr(settings, field, encrypted)
        action = "updated"
        
    db.add(APIKeyUsage(provider=update.provider, operation=f"key_{action}", success=True))
    db.commit()
    return {"status": "success", "action": action}

@router.post("/preferences")
async def update_preferences(prefs: UserPreferences, db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter_by(is_active=1).first()
    if not settings:
        settings = UserSettings(is_active=1)
        db.add(settings)
        
    data = prefs.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(settings, k, v) # Handles int/bool conversion automatically? SQLAlchemy Integer type handles Python bool.
        
    db.commit()
    return {"status": "success"}
