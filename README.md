# 🌊 OpenManus (Agent-S3 + Surf)

**OpenManus** is an open-source, agentic platform for computer use. It combines the advanced reasoning and vision of **Agent-S3** with the **Surf** user interface, executing safely within **E2B Sandboxes**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

## 🏗 Architecture

| Component       | Tech Stack           | Role                                           |
| --------------- | -------------------- | ---------------------------------------------- |
| **🧠 Brain**     | **Python (FastAPI)** | Runs Agent-S3, handles reasoning & planning    |
| **👁️ Eyes**      | **UI-TARS**          | Vision model for precise GUI element grounding |
| **🖥️ Interface** | **Next.js (React)**  | User facing chat & stream viewer               |
| **📦 Sandbox**   | **E2B Cloud**        | Secure, isolated environment for execution     |

## 🚀 Getting Started

### Prerequisites
- **Docker** & **Docker Compose**
- **OpenAI API Key** (for GPT-5/4o)
- **E2B API Key** (for Sandbox)
- **Local vLLM** (for UI-TARS Vision)

### 1. Configuration
Create `.env` files:

**`backend/.env`**:
```ini
OPENAI_API_KEY=sk-...
E2B_API_KEY=e2b_...
VISION_SERVICE_URL=http://host.docker.internal:8080/v1
```

**`frontend/.env.local`** (Optional, defaults to localhost):
```ini
BACKEND_URL=http://localhost:8000
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)

### 3. Vision Service (Required)
You must run the UI-TARS model locally or on a GPU server.
```bash
# Example vLLM command
vllm serve ByteDance-Seed/UI-TARS-1.5-7B --port 8080 --trust-remote-code
```

## 🛠 Manual Installation

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m backend.app.main
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📄 License
MIT
