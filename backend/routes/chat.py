from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.services.agent_service import AgentService
import json
import asyncio

router = APIRouter()
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
        # 1. Initialize Sandbox
        res = resolution if resolution and len(resolution) == 2 else None
        info = agent_service.initialize_sandbox(resolution=res)
        
        yield f"event: sandbox_created\ndata: {json.dumps({'sandboxId': info['sandbox_id'], 'vncUrl': info['vnc_url']})}\n\n"
        yield f"event: reasoning\ndata: {json.dumps({'content': 'Initializing Agent (V0.1 LangGraph)...'})}\n\n"
        
        # 2. Run LangGraph Agent
        if not agent_service.langgraph_agent:
             yield f"event: error\ndata: {json.dumps({'content': 'LangGraph functionality is not enabled or failed to initialize.'})}\n\n"
             return

        # V0.1: Use LangGraph Runner
        stream = agent_service.langgraph_agent.run(instruction, user_image=image)
        
        pending_actions = []

        for output in stream:
            # Handle Agent Node Output
            if "agent" in output:
                payload = output["agent"]
                logs = payload.get("logs", [])
                actions = payload.get("latest_actions", [])
                status = payload.get("status", "running")
                info = payload.get("info", {})
                
                # Yield Logs/Reasoning
                for log in logs:
                    yield f"event: reasoning\ndata: {json.dumps({'content': log})}\n\n"
                
                # Yield Plan/Thought
                plan = info.get("plan", "")
                if plan:
                    clean_plan = plan.split("```")[0].strip() # Simple heuristic
                    if clean_plan:
                         yield f"event: reasoning\ndata: {json.dumps({'content': clean_plan})}\n\n"
                
                # Check outcome BEFORE actions (if immediate done)
                if status == "done":
                    final_msg = "Task completed successfully."
                    if actions: # If explicit DONE action
                         final_msg = "Task completed."
                    yield f"event: done\ndata: {json.dumps({'content': final_msg})}\n\n"
                    break
                elif status == "fail":
                    yield f"event: done\ndata: {json.dumps({'content': 'Task failed.'})}\n\n"
                    break
                
                # Yield Actions
                pending_actions = actions # Track for completion in tool node
                for action in actions:
                    action_payload = {
                        "type": "computer_action",
                        "action_type": "execute",
                        "code": action
                    }
                    yield f"event: action\ndata: {json.dumps({'action': action_payload})}\n\n"
                    await asyncio.sleep(0.1)

            # Handle Tool Node Output
            elif "tools" in output:
                payload = output["tools"]
                logs = payload.get("logs", [])
                
                # Yield Tool Logs
                for log in logs:
                    yield f"event: reasoning\ndata: {json.dumps({'content': log})}\n\n"
                
                # Mark pending actions as completed
                for _ in pending_actions:
                    yield f"event: action_completed\ndata: {json.dumps({})}\n\n"
                pending_actions = []

            # Handle unexpected structure
            else:
                pass
                
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

