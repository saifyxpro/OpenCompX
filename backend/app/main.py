from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat
import uvicorn

app = FastAPI(title="OpenManus Agent S3 Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Chat Router
app.include_router(chat.router, prefix="/api") # or just app.include_router(chat.router) depending on frontend.
# Frontend calls /api/chat in useChat? No, it calls /api/chat in next.js, which proxies to backend. 
# Wait, frontend uses `fetch("/api/chat")`. Next.js likely proxies /api/chat -> backend/chat.
# Let's check next.config.mjs or just enable /chat directly on root to be safe, or include without prefix if frontend calls backend directly.
# The original code had @app.post("/chat").
# So I should include it at root.

app.include_router(chat.router)

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
