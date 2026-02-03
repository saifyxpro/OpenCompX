# 🚀 OpenManus Production Setup

Run the entire OpenManus stack (Frontend + Backend) with a single command using Docker Compose.

## Prerequisites

1.  **Docker** & **Docker Compose** installed.
2.  **vLLM** (Vision Model) running separately (usually on your GPU machine).
    *   `vllm serve ByteDance-Seed/UI-TARS-1.5-7B ...`

## 📦 How to Run

1.  **Configure Environment:**
    Ensure `backend/.env` is set up (API Keys, Vision URL).
    *   If vLLM is on the host, use `http://host.docker.internal:8080/v1` or the cloud URL.

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
