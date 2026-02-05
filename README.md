# 🌊 OpenCompX

**OpenCompX** is an open-source, agentic platform for computer use, capable of executing complex tasks autonomously. It combines advanced AI reasoning (supporting both Google Gemini 2.0 Flash and OpenAI GPT-4o) with real-time vision capabilities via UI-TARS.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)

## 🌟 What's New in V0.1 (LangGraph Agent)

-   **🧠 LangGraph Architecture**: Transitioned from a rigid loop to a stateful, graph-based agent using **LangGraph**. This enables complex multi-step reasoning, error recovery, and future human-in-the-loop capabilities.
-   **⚡ Turbo Mode V2**: Optimized execution pipeline with reduced latency. Action execution is now significantly faster (0.1s delay vs 1.5s).
-   **🎨 Enhanced UI**: A completely redesigned chat interface with:
    -   **Task Timer**: Real-time tracking of task duration.
    -   **Stop Button**: Immediate cancellation of running agents.
    -   **Minimal Loading State**: Cleaner, less intrusive status indicators.
-   **💰 Cost Optimization**: Implemented a "Text-Only Planner" mode that reduces token usage by selectively sharing screenshots only with the grounding model (UI-TARS) and not the reasoning planner.

## 🏗 Architecture

| Component       | Tech Stack             | Role                                                                 |
| :-------------- | :--------------------- | :------------------------------------------------------------------- |
| **🧠 Brain**     | **Python (LangGraph)** | Orchestrates the agent workflow (Planner -> Tools -> Planner).       |
| **👁️ Eyes**      | **UI-TARS**            | Vision model for precise GUI element grounding and coordinates.      |
| **🖥️ Interface** | **Next.js (React)**    | Premium Chat UI, Live Desktop Stream (VNC), and real-time logs.      |
| **📦 Sandbox**   | **Docker / E2B**       | Secure, isolated environment for execution with pre-installed tools. |

## 🚀 Getting Started

### Prerequisites

-   **Docker** & **Docker Compose**
-   **Google API Key** (for Gemini 2.0 Flash) OR **OpenAI API Key**
-   **Local vLLM** (for UI-TARS Vision)

### 1. Configuration

Create `.env` file in `backend/`:

**`backend/.env`**:

```ini
# Provider Selection: 'google' or 'openai'
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp

# API Keys
GOOGLE_API_KEY=AIz...
# OPENAI_API_KEY=sk-... (If using OpenAI)

# Vision Service (UI-TARS)
VISION_SERVICE_URL=http://host.docker.internal:8080/v1
VISION_MODEL=ByteDance-Seed/UI-TARS-7B-DPO
```

### 2. Run with Docker Compose

Run the entire stack (Frontend + Backend + Sandbox) with a single command:

```bash
docker-compose up --build -d
```

-   **Frontend UI**: [http://localhost:3000](http://localhost:3000)
-   **Backend API**: [http://localhost:8000](http://localhost:8000)

### 3. Vision Service (Required)

You must run the UI-TARS model locally or on a GPU server.

```bash
# Run with optimized settings for 24GB GPU
vllm serve ByteDance-Seed/UI-TARS-7B-DPO \
  --port 8080 \
  --trust-remote-code \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90 \
  --disable-log-stats
```

## 🛠 Manual Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 💡 Usage Tips

-   **Task Timer**: Watch the top bar to see how long your task takes.
-   **Stop Execution**: Hit the red "Stop" square button at any time to halt the agent.
-   **Restarting**: If you update the backend code, always restart the python process or docker container to apply changes.

## 📄 License

MIT
