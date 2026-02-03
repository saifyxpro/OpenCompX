![Surf Preview](/readme-assets/surf-light.png#gh-light-mode-only)

# 🏄 OpenManus - Local AI Computer Use Agent

A Next.js application that allows AI to interact with a local virtual desktop environment via Docker. This project integrates a local Docker container running XFCE+VNC with OpenAI's API to create an AI agent that can perform tasks on your computer (sandboxed) through natural language instructions.

## Overview

OpenManus provides a web interface where users can:

1. Start a local virtual desktop sandbox environment (Docker)
2. Send natural language instructions to an AI agent
3. Watch as the AI agent performs actions on the virtual desktop
4. Interact with the AI through a chat interface

The application uses Server-Sent Events (SSE) to stream AI responses and actions in real-time.

## Architecture

1. **Frontend UI (Next.js)**: Chat interface & VNC viewer
2. **Local Docker Container**: Runs Ubuntu + XFCE + VNC + Firefox
3. **Backend API (FastAPI)**: Controls the Docker container via `docker exec`
4. **Agent S3**: Intelligent agent that plans and executes actions

## Setup Instructions

1. **Prerequisites**
   - Docker Desktop installed and running
   - Node.js & npm
   - Python 3.10+

2. **Clone the repository**
   ```bash
   git clone https://github.com/saifyxpro/OpenManus
   cd OpenManus
   ```

3. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # create .env file with OPENAI_API_KEY
   python main.py
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Start the Local Desktop Container**
   The backend will automatically start the Docker container when you send your first message!
   
   Or manually:
   ```bash
   docker compose -f docker-compose.desktop.yml up -d
   ```

6. **Open the App**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Features

- **Local Execution**: No cloud dependencies, runs entirely on your machine
- **Docker Isolation**: Actions happen inside a container, keeping your host safe
- **Real-Time View**: See what the agent sees via VNC streaming
- **Agent S3 Integration**: State-of-the-art GUI agent capabilities

## License

Apache 2.0
