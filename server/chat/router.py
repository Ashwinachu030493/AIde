from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import asyncio
from server.llm.client import LLMClient
from server.shared.vector_store import VectorStore
# from server.models.chat import ChatMessage # Usage implied via dict for now

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
llm_client = LLMClient()
vector_store = VectorStore()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Expecting JSON string or text provided by client
            # The client sends plain text for MVP phase 1, but we should parse relevant data
            # For backward compatibility with Phase 1 frontend, we handle text.
            # Ideally frontend sends JSON.
            
            data = await websocket.receive_text()
            logger.info(f"Received: {data}")

            # 1. Retrieval (RAG) - Async non-blocking
            # (Mock project ID for now, or extract from message if we had protocol)
            # relevant_code = await vector_store.query_similar_code(project_id="default", query=data)
            
            # 2. Build Prompt
            system_prompt = "You are AIde, a helpful coding assistant. Use markdown for code."
            
            # 3. Stream LLM Response
            full_response = ""
            
            # Send immediate ACK or typing
            # await websocket.send_text("Typing...") 

            try:
                async for chunk in llm_client.get_completion(
                    prompt=data, 
                    system_prompt=system_prompt,
                    streaming=True
                ):
                    full_response += chunk
                    await websocket.send_text(chunk) # Stream back raw text chunks
                
                # In a real protocol we might send a "DONE" signal
            except Exception as e:
                logger.error(f"LLM Error: {e}")
                await websocket.send_text(f"Error: {str(e)}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
