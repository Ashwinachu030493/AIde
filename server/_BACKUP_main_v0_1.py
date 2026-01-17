from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.chat.router import router as chat_router
from server.ingestion.router import router as ingestion_router
from server.settings.router_simple import router as settings_router
from server.audit.router import router as audit_router

app = FastAPI(title="AIde Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(ingestion_router)
app.include_router(settings_router)
app.include_router(audit_router)

@app.on_event("startup")
async def on_startup():
    from server.shared.database import init_db
    # Import models so tables are created
    from server.models import user_simple 
    init_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AIde Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
