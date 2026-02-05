# 🌊 OpenCompX

**OpenCompX** is an open-source, agentic platform for computer use, capable of executing complex tasks autonomously. It combines advanced AI reasoning (supporting both Google Gemini 3 Flash and OpenAI GPT-5) with real-time vision capabilities via UI-TARS.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

## 🏗 Architecture

| Component       | Tech Stack           | Role                                             |
| --------------- | -------------------- | ------------------------------------------------ |
| **🧠 Brain**     | **Python (FastAPI)** | Runs Agent-S3, handles reasoning (Gemini/OpenAI) |
| **👁️ Eyes**      | **UI-TARS**          | Vision model for precise GUI element grounding   |
| **🖥️ Interface** | **Next.js (React)**  | Premium Chat UI & Live Desktop Stream            |
| **📦 Sandbox**   | **Docker / E2B**     | Secure, isolated environment for execution       |

## 🚀 Getting Started

### Prerequisites
- **Docker** & **Docker Compose**
- **Google API Key** (for Gemini 3 Flash - Free/High Speed) OR **OpenAI API Key**
- **Local vLLM** (for UI-TARS Vision)

### 1. Configuration
Create `.env` file in `backend/`:

**`backend/.env`**:
```ini
# Provider Selection: 'google' or 'openai'
LLM_PROVIDER=google
LLM_MODEL=gemini-3-flash-preview

# API Keys
GOOGLE_API_KEY=AIz...
# OPENAI_API_KEY=sk-... (If using OpenAI)

VISION_SERVICE_URL=http://host.docker.internal:8080/v1
VISION_MODEL=ByteDance-Seed/UI-TARS-1.5-7B
```

### 2. Run with Docker Compose
Run the entire stack (Frontend + Backend + Sandbox) with a single command:
```bash
docker-compose up --build -d
```
- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

### 3. Vision Service (Required)
You must run the UI-TARS model locally or on a GPU server.
```bash
# Run with optimized settings for 24GB GPU
vllm serve ByteDance-Seed/UI-TARS-1.5-7B \
  --port 8080 \
  --trust-remote-code \
  --max-model-len 24576 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 4 \
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

## 📄 License
MIT
