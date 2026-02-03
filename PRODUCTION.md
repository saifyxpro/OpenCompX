# 🚀 OpenCompX Production Setup

Run the entire **OpenCompX** stack (Frontend + Backend) within a production Docker environment.

## Prerequisites

1.  **Docker** & **Docker Compose** installed.
2.  **vLLM** (Vision Model) running separately (usually on your GPU machine).
    *   `vllm serve ByteDance-Seed/UI-TARS-1.5-7B ...`

## 📦 How to Run

1.  **Configure Environment:**
    Ensure `backend/.env` is set up with your preferred provider:
    ```ini
    LLM_PROVIDER=google
    LLM_MODEL=gemini-3-flash-preview
    GOOGLE_API_KEY=AIza...
    ```

2.  **Start Services:**
    ```bash
    docker-compose up --build -d
    ```

3.  **Access:**
    *   **UI:** [http://localhost:3000](http://localhost:3000)
    *   **API:** [http://localhost:8000/docs](http://localhost:8000/docs)

4.  **Stop:**
    ```bash
    docker-compose down
    ```

## ⚠️ Important Notes

*   **Docker-in-Docker:** The backend container mounts `/var/run/docker.sock` so it can spawn the "Sandbox" containers (where the agent actually runs). This is required.
*   **Networking:** The Frontend talks to the Backend via the client's browser, so `localhost:8000` usually works fine if you are accessing it locally.
