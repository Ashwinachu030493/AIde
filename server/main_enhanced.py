import logging
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.auditor.router_persistent import router as auditor_router
from server.chat.router_enhanced import router as chat_router
from server.dashboard.router_simple import router as dashboard_router
from server.ingestion.router import router as ingestion_router
from server.settings.router_simple import router as settings_router
from server.shared.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIde API (Enhanced)",
    description="AI-powered coding assistant with user settings and persistent audit",
    version="0.3.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(ingestion_router)
app.include_router(settings_router)
app.include_router(auditor_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    """Health check with version info"""
    return {
        "status": "healthy",
        "service": "AIde API",
        "version": "0.3.0",
        "features": {
            "chat": "enhanced with user settings",
            "ingestion": "complete",
            "settings": "encrypted API keys",
            "auditor": "persistent w/ sqlite",
        },
    }


@app.get("/health/detailed")
async def detailed_health(db=Depends(get_db)):
    """Detailed health check including settings"""
    from server.services.settings_loader import SettingsLoader

    settings_loader = SettingsLoader()
    user_settings = settings_loader.load_user_settings(db)

    health_status = {
        "api": "ok",
        "database": "connected",
        "has_user_settings": user_settings is not None,
        "llm_providers_configured": 0,
    }

    if user_settings:
        providers = ["openai", "anthropic", "groq"]
        configured = sum(1 for p in providers if user_settings.get(f"{p}_api_key"))
        health_status["llm_providers_configured"] = configured

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main_enhanced:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
