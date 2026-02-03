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
    """Generate SSE events with proper structured format for frontend consumption."""
    
    try:
        # 1. Initialize Sandbox if needed
        if not agent_service.container_running:
             res = resolution if resolution and len(resolution) == 2 else None
             info = agent_service.initialize_sandbox(resolution=res)
             # Yield sandbox info - CRITICAL: frontend needs sandboxId and vncUrl
             yield f"event: sandbox_created\ndata: {json.dumps({'sandboxId': info['sandbox_id'], 'vncUrl': info['vnc_url']})}\n\n"
        
        # 2. Start Agent Step
        yield f"event: reasoning\ndata: {json.dumps({'content': 'Analyzing screen and planning actions...'})}\n\n"
        
        # Run agent step (blocking, uses thread pool)
        result = await asyncio.to_thread(agent_service.step, instruction)
        
        if result["status"] == "error":
             yield f"event: error\ndata: {json.dumps({'content': result['message']})}\n\n"
             return

        # 3. Yield Agent's reasoning/plan if available
        if result.get("info"):
             plan = result["info"].get("plan", "")
             if plan:
                 yield f"event: reasoning\ndata: {json.dumps({'content': plan})}\n\n"

        # 4. Yield each action with structured format for UI action cards
        actions = result.get("actions", [])
        logs = result.get("logs", [])
        
        for i, action in enumerate(actions):
            # Send action event - frontend will show pending action card
            action_payload = {
                "type": "computer_action",
                "action_type": "execute",
                "code": action
            }
            yield f"event: action\ndata: {json.dumps({'action': action_payload})}\n\n"
            
            # Small delay to make UI feel responsive
            await asyncio.sleep(0.1)
            
            # Send corresponding log as reasoning
            if i < len(logs):
                yield f"event: reasoning\ndata: {json.dumps({'content': logs[i]})}\n\n"
            
            # Send action_completed event - frontend will update card to completed
            yield f"event: action_completed\ndata: {json.dumps({})}\n\n"
        
        # 5. If there are more logs than actions (status messages)
        for log in logs[len(actions):]:
            yield f"event: reasoning\ndata: {json.dumps({'content': log})}\n\n"

        # 6. Done
        yield f"event: done\ndata: {json.dumps({'content': 'Task completed'})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'content': str(e)})}\n\n"

@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests and stream responses."""
    # Extract latest user message
    last_message = request.messages[-1]["content"]
    
    return StreamingResponse(
        event_generator(last_message, request.sandboxId, request.resolution),
        media_type="text/event-stream"
    )

