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
    image: str | None = None
    selectedTool: str | None = None

    class Config:
        extra = "ignore"

async def event_generator(instruction: str, existing_sandbox_id: str | None, resolution: list[int] | None, reset_env: bool = False, image: str | None = None, selectedTool: str | None = None):
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
        
        # 3. Start Agent Loop for Max 10 steps
        executed_count = 0
        
        for step in range(10):
            # Run one step (blocking inside thread)
            # Pass reset_env only for step 0
            should_reset = reset_env if step == 0 else False
            result = await asyncio.to_thread(agent_service.execute_next_step, instruction, step, executed_count, should_reset, image=image, selectedTool=selectedTool)
            
            if result["status"] == "error":
                 yield f"event: error\ndata: {json.dumps({'content': result['message']})}\n\n"
                 return

            # Yield reasoning/plan
            if result.get("info"):
                 plan = result["info"].get("plan", "")
                 if plan:
                     yield f"event: reasoning\ndata: {json.dumps({'content': plan})}\n\n"

            # Yield actions and logs
            actions = result.get("actions", [])
            logs = result.get("logs", [])
            executed_count += len(actions)
            
            for i, action in enumerate(actions):
                # Send action event
                action_payload = {
                    "type": "computer_action",
                    "action_type": "execute",
                    "code": action
                }
                yield f"event: action\ndata: {json.dumps({'action': action_payload})}\n\n"
                
                await asyncio.sleep(0.1)
                
                # Corresponding log
                if i < len(logs):
                    yield f"event: reasoning\ndata: {json.dumps({'content': logs[i]})}\n\n"
                
                # Complete the action card
                yield f"event: action_completed\ndata: {json.dumps({})}\n\n"
            
            # Remaining logs
            for log in logs[len(actions):]:
                yield f"event: reasoning\ndata: {json.dumps({'content': log})}\n\n"

            # Check termination
            if result["status"] == "done":
                yield f"event: done\ndata: {json.dumps({'content': 'Task completed'})}\n\n"
                break
            elif result["status"] == "fail":
                yield f"event: done\ndata: {json.dumps({'content': 'Task failed'})}\n\n"
                break
            
            # Important: Keep-alive / pacing
            await asyncio.sleep(0.1)

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'content': str(e)})}\n\n"

@router.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests and stream responses."""
    # Extract latest user message
    last_message = request.messages[-1]["content"]
    
    # Determine if we should reset the environment (New conversation or clear chat)
    # If explicit sandboxId is NOT provided, it might mean new session? 
    # Or rely on message length?
    # If messages length is 1 (just the new prompt), we clean up.
    should_reset_env = len(request.messages) == 1
    
    return StreamingResponse(
        event_generator(last_message, request.sandboxId, request.resolution, should_reset_env, request.image, request.selectedTool),
        media_type="text/event-stream"
    )

