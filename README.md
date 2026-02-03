# 🌊 OpenManus

**OpenManus** is an open-source, agentic platform for computer use. It combines advanced AI reasoning with real-time vision capabilities to autonomously perform tasks on a computer, executing safely within isolated environments.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

## 🏗 Architecture

| Component       | Tech Stack           | Role                                           |
| --------------- | -------------------- | ---------------------------------------------- |
| **🧠 Brain**     | **Python (FastAPI)** | Runs Agent-S3, handles reasoning & planning    |
| **👁️ Eyes**      | **UI-TARS**          | Vision model for precise GUI element grounding |
| **🖥️ Interface** | **Next.js (React)**  | Premium Chat UI & Live Desktop Stream          |
| **📦 Sandbox**   | **Docker / E2B**     | Secure, isolated environment for execution     |

## 🚀 Getting Started

### Prerequisites
- **Docker** & **Docker Compose**
- **OpenAI API Key** (for GPT-4o / GPT-5)
- **Local vLLM** (for UI-TARS Vision)
- *(Optional)* **E2B API Key** (if using Cloud Sandboxes)

### 1. Configuration
Create `.env` file in `backend/`:

**`backend/.env`**:
```ini
OPENAI_API_KEY=sk-...
VISION_SERVICE_URL=http://host.docker.internal:8080/v1
# E2B_API_KEY=e2b_... (Only if using cloud)
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
# Example vLLM command (Requires GPU)
vllm serve ByteDance-Seed/UI-TARS-1.5-7B --port 8080 --trust-remote-code
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
