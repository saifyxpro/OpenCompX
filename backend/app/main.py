
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.agent.wrapper import AgentWrapper
import uvicorn
import os

app = FastAPI(title="OpenManus Agent S3 Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
agent_service = AgentWrapper()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    status: str
    info: dict | None = None
    actions: list | None = None
    logs: list[str] = []

@app.get("/health")
def health_check():
    return {"status": "running", "agent_initialized": agent_service.agent is not None}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    print(f"Received instruction: {request.message}")
    result = agent_service.step(request.message)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
