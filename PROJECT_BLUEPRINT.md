# OpenManus Project Blueprint: Agent-S3 Integration

## 1. Project Overview

**OpenManus** (formerly Surf) is a hybrid-compute GUI automation platform.
- **Frontend**: Next.js 16 Web Interface (User Control Center).
- **Backend**: Python Service running **Agent-S3** (State-of-the-Art Computer Use Agent).
- **Goal**: Enable natural language control of a local or remote Linux/Windows machine using the advanced `Agent-S3` framework.

## 2. Architecture

```mermaid
graph TD
    User[User] -->|Chat/Commands| Frontend[OpenManus Frontend (Next.js)]
    Frontend -->|WebSocket/API| Backend[Agent Service (Python/FastAPI)]
    
    subgraph "Backend Server (Linux GPU Machine)"
        Backend -->|Controls| Env[Local Environment / E2B]
        Backend -->|Uses| AgentS3[Agent-S3 Library]
        AgentS3 -->|Inference| Model[GPT-5.2 / Custom Model]
        AgentS3 -->|Vision| UITars[UI-TARS-1.5-7B]
    end
```

## 3. Directory Structure

```text
OpenManus/
├── frontend/                 # (Existing Surf Codebase)
│   ├── app/
│   ├── components/
│   └── lib/
│       └── api.ts            # [NEW] Client for Backend API
│
├── backend/                  # [NEW] Python Agent Service
│   ├── app/
│   │   ├── main.py           # FastAPI Entrypoint
│   │   ├── api.py            # Endpoints
│   │   └── socket.py         # Real-time Streaming
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── wrapper.py        # Agent-S3 Wrapper Class
│   │   └── config.py         # Model/Env Config
│   ├── requirements.txt
│   └── .env
│
└── PROJECT_BLUEPRINT.md
```

## 4. Implementation Details

### Frontend (Next.js) modification
The current Surf frontend communicates directly with LLMs and E2B via API routes. We will modify it to act as a **Interface** for our custom Backend.
- **Remove**: Direct E2B/LLM calls in `api/chat/route.ts`.
- **Add**: API Client to forward messages to `http://localhost:8000` (Backend).
- **Stream**: Render the VNC stream provided by the backend.

### Backend (Python Agent-S3)
We will create a robust FastAPI service that hosts the `Agent-S3` logic.

#### Prerequisites
- **OS**: Linux (Preferred) or Windows.
- **Hardware**: GPU with 24GB+ VRAM (for UI-TARS) OR usage of Hosted Inference.
- **Env**: Python 3.10+

#### Core Components
1.  **Orchestrator**: Manages the `AgentS3` instance.
2.  **Vision Loop**: Captures screenshots -> Sends to Agent-S3 -> Executes Action.
3.  **API**: Exposes:
    - `POST /start`: Initialize agent/sandbox.
    - `POST /chat`: Send instruction.
    - `WS /stream`: Stream logs/screenshots/desktop view.

## 5. Development Steps

1.  **Setup Backend Structure**: Create `backend/` directories and core Python files.
2.  **Integrate Agent-S3**: Write `backend/agent/wrapper.py` to initialize `AgentS3` from `gui_agents` library.
3.  **Frontend Connection**: Update `frontend/src/lib/chat-context` to talk to our custom backend.
4.  **Deployment**: Instructions for running the Python backend on a Linux GPU machine.

## 6. Agent-S3 Configuration (Target)
```python
# backend/agent/config.py
PROVIDER = "openai"
MODEL = "gpt-5-2025-08-07"
GROUNDING_MODEL = "ui-tars-1.5-7b"
GROUNDING_URL = "http://localhost:8080" # Local VLLM/SGLang
```
