from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.services.agent_service import AgentService
import json
import asyncio

router = APIRouter()

# Initialize Agent Service (Singleton dependent on lifecycle, but global for now)
agent_service = AgentService()

class ChatRequest(BaseModel):
    messages: list
    sandboxId: str | None = None
    model: str = "openai"
    resolution: list[int] | None = None

    class Config:
        extra = "ignore"

async def event_generator(instruction: str, existing_sandbox_id: str | None, resolution: list[int] | None):
    # 1. Initialize Sandbox if needed
    if not agent_service.sandbox:
         # Pass resolution ensuring it checks for None
         res = resolution if resolution and len(resolution) == 2 else None
         info = agent_service.initialize_sandbox(resolution=res)
         # Yield sandbox info
         yield f"event: sandbox_created\ndata: {json.dumps({'sandboxId': info['sandbox_id'], 'vncUrl': info['vnc_url']})}\n\n"
    
    # 2. Run Agent Step
    yield f"event: reasoning\ndata: Processing instruction...\n\n"
    
    try:
        # This is blocking, might take seconds
        result = await asyncio.to_thread(agent_service.step, instruction)
        
        if result["status"] == "error":
             yield f"event: error\ndata: {result['message']}\n\n"
             return

        # Yield Reasoning (Info)
        if result.get("info"):
             yield f"event: reasoning\ndata: {json.dumps(result['info'])}\n\n"

        # Yield Execution Logs (Human-Like)
        if result.get("logs"):
            for log in result["logs"]:
                yield f"event: reasoning\ndata: {log}\n\n"
        
        # Actions are handled in logs now, but if we need structured actions later:
        if result.get("actions"):
             pass 

        yield f"event: done\ndata: [DONE]\n\n"

    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"

@router.post("/chat")
async def chat(request: ChatRequest):
    # Extract latest user message
    last_message = request.messages[-1]["content"]
    
    return StreamingResponse(
        event_generator(last_message, request.sandboxId, request.resolution),
        media_type="text/event-stream"
    )
