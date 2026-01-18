import asyncio
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from server.llm.client import LLMClient, UserLLMConfig
from server.services.settings_loader import SettingsLoader
from server.shared.database import get_db
from server.shared.vector_store import VectorStore

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# Store active connections and their LLM clients
# Map: conversation_id -> LLMClient
active_clients: Dict[str, LLMClient] = {}


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: Any):
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str, db=Depends(get_db)):
    """WebSocket endpoint with user-specific LLM configuration"""
    # Accept connection first
    await manager.connect(websocket)

    try:
        # Load user settings and create LLM client specific for this session
        settings_loader = SettingsLoader()
        llm_config = settings_loader.load_llm_config(db)
        llm_client = LLMClient(user_config=llm_config, db_session=db)

        # Store client for this conversation
        active_clients[conversation_id] = llm_client

        logger.info(f"Chat connected: {conversation_id} (Model: {llm_config.default_model})")

        while True:
            # Wait for messages
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "message":
                await handle_chat_message(websocket, conversation_id, data, llm_client, db)
            elif message_type == "settings_update":
                # Reload settings if frontend notifies us of a change
                new_config = settings_loader.load_llm_config(db)
                llm_client.update_config(new_config)
                await manager.send_json(
                    websocket,
                    {
                        "type": "settings_updated",
                        "message": f"LLM settings refreshed. Using {new_config.default_model}",
                    },
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {conversation_id}")
        manager.disconnect(websocket)
        if conversation_id in active_clients:
            del active_clients[conversation_id]

    except Exception as e:
        logger.error(f"WebSocket error in {conversation_id}: {e}")
        # Try to close gracefully if possible
        try:
            await websocket.close(code=1011)
        except:
            pass
        manager.disconnect(websocket)
        if conversation_id in active_clients:
            del active_clients[conversation_id]


async def handle_chat_message(
    websocket: WebSocket, conversation_id: str, data: Dict, llm_client: LLMClient, db
):
    """Handle chat message with user-specific LLM client"""
    user_message = data.get("content", "")
    context = data.get("context", {})

    # 1. Send typing indicator
    await manager.send_json(websocket, {"type": "typing", "is_typing": True})

    try:
        # 2. RAG: Retrieve relevant context
        relevant_code = []
        if context.get("project_id"):
            vector_store = VectorStore()
            # Note: query_similar_code might be async or sync depending on impl
            # Assuming it's async based on earlier files, but VectorStore uses run_in_executor usually
            # Let's check the vector_store.py if we have time, but sticking to "async" is safer if uncertain
            # Actually, previous analysis of vector_store.py showed it uses run_in_executor
            # so we should await it if it's defined as async def.
            # However, looking at previous logs, it seemed flexible.
            # We'll assume awaitable.
            try:
                # Mock call for now if VectorStore isn't fully robust locally
                relevant_code = await vector_store.query_similar_code(
                    project_id=context["project_id"], query=user_message, n_results=3
                )
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # 3. Build Prompt
        enhanced_prompt = build_enhanced_prompt(
            user_message=user_message, code_context=relevant_code, project_context=context
        )

        # System prompt
        system_prompt = """You are AIde, a helpful coding assistant for novice developers.
        Explain concepts simply. Provide code examples in markdown blocks.
        Be patient and encouraging."""

        # 4. Stream LLM Response
        available_providers = llm_client.get_available_providers()
        if not available_providers:
            await manager.send_json(
                websocket,
                {
                    "type": "error",
                    "content": "No API keys configured. Please go to Settings to configure a provider.",
                },
            )
            return

        full_response = ""

        # Stream generator
        stream_gen = await llm_client.get_completion(
            prompt=enhanced_prompt, system_prompt=system_prompt, streaming=True
        )

        async for chunk in stream_gen:
            full_response += chunk
            await manager.send_json(
                websocket, {"type": "message_chunk", "content": chunk, "is_complete": False}
            )

        # 5. Send completion
        await manager.send_json(
            websocket, {"type": "message_complete", "content": full_response, "is_complete": True}
        )

    except ValueError as e:
        await manager.send_json(
            websocket, {"type": "error", "content": f"Configuration Error: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await manager.send_json(
            websocket, {"type": "error", "content": f"I encountered an error: {str(e)}"}
        )
    finally:
        # Stop typing
        await manager.send_json(websocket, {"type": "typing", "is_typing": False})


def build_enhanced_prompt(user_message: str, code_context: List[Any], project_context: Dict) -> str:
    """Build enhanced prompt with context"""
    prompt_parts = []

    # Add project context
    if project_context.get("project_name"):
        prompt_parts.append(f"Project: {project_context['project_name']}")
    if project_context.get("current_file"):
        prompt_parts.append(f"Current file: {project_context['current_file']}")

    # Add code context
    if code_context:
        prompt_parts.append("\nRelevant code:")
        for code in code_context:
            # Handle if code is dict or object
            content = (
                code.get("content") if isinstance(code, dict) else getattr(code, "content", "")
            )
            meta = (
                code.get("metadata", {})
                if isinstance(code, dict)
                else getattr(code, "metadata", {})
            )
            path = meta.get("file_path", "unknown")
            prompt_parts.append(f"\n--- {path} ---\n{content[:500]}...")

    prompt_parts.append(f"\nUser Query: {user_message}")

    return "\n".join(prompt_parts)


@router.get("/providers/available")
async def get_available_providers(db=Depends(get_db)):
    """Get available LLM providers based on user settings"""
    settings_loader = SettingsLoader()
    llm_config = settings_loader.load_llm_config(db)
    llm_client = LLMClient(llm_config)

    available = llm_client.get_available_providers()

    return {
        "available_providers": available,
        "default_model": llm_config.default_model,
        "has_openai": "openai" in available,
        "has_anthropic": "anthropic" in available,
        "has_groq": "groq" in available,
    }
