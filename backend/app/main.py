
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.agent.wrapper import AgentWrapper
import uvicorn
import json
import asyncio

app = FastAPI(title="OpenManus Agent S3 Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
agent_service = AgentWrapper()

class ChatRequest(BaseModel):
    messages: list
    sandboxId: str | None = None
    model: str = "openai"

    class Config:
        extra = "ignore"

async def event_generator(instruction: str, existing_sandbox_id: str | None):
    # 1. Initialize Sandbox if needed
    if not agent_service.sandbox:
         info = agent_service.initialize_sandbox()
         # Yield sandbox info
         yield f"event: sandbox_created\ndata: {json.dumps({'sandboxId': info['sandbox_id'], 'vncUrl': info['vnc_url']})}\n\n"
    
    # 2. Run Agent Step (Streaming wrapper needed for real streaming, but for now we simulate)
    # Agent-S3 step() is blocking. We can't easily stream internal thoughts unless we modify Agent-S3 
    # or if Agent-S3 supports callbacks. 
    # For this MVP, we will yield "reasoning" then "action".
    
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

        if result.get("actions"):
            for action in result["actions"]:
                # Construct action object compatible with frontend expectations if possible?
                # Surf expects specific action types. Agent-S3 returns code strings.
                # We send a generic 'tool_use' or just log it as reasoning for now 
                # strictly speaking Surf expects structured actions for visualization.
                # We will send them as 'reasoning' updates to show what's happening.
                # Construct action object compatible with frontend expectations if possible?
                # Surf expects specific action types. Agent-S3 returns code strings.
                # We send a generic 'tool_use' or just log it as reasoning for now 
                # strictly speaking Surf expects structured actions for visualization.
                # We will send them as 'reasoning' updates to show what's happening.
                # PER USER REQUEST: DISABLE ALL LOGS
                pass
                
                # We could try to map to 'click', 'type' events if we parsed the python code.
                # But for now, text feedback is safer.
                
        yield f"event: done\ndata: [DONE]\n\n"

    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"

@app.post("/chat")
async def chat(request: ChatRequest):
    # Extract latest user message
    # Surf sends full conversation history.
    last_message = request.messages[-1]["content"]
    
    return StreamingResponse(
        event_generator(last_message, request.sandboxId),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
