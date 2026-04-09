"""FastAPI application entry point for Rentor AI Agents."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import PORT
from src.chat.google_chat import router as chat_router
from src.agents.agent_manager import register_user, handle_message
from src.models.schemas import AgentUser, IncomingMessage, MessageSource, VideoCallRequest
from src.video.pika_manager import join_meeting, leave_meeting
from src.knowledge.policy_loader import list_policies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    print("Rentor AI Agents starting up...")
    print(f"Available policies: {list_policies()}")
    yield
    print("Rentor AI Agents shutting down.")


app = FastAPI(
    title="Rentor AI Agents",
    description="Personal AI agents for Rentor property management team",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount Google Chat webhook router
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Rentor AI Agents",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "register_user": "POST /api/users",
            "send_message": "POST /api/message",
            "google_chat_webhook": "POST /chat/webhook",
            "video_join": "POST /api/video/join",
            "video_leave": "POST /api/video/leave/{user_id}",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "rentor-ai-agents"}


@app.post("/api/users")
async def create_user(user: AgentUser):
    """Register a new team member with a personal agent."""
    register_user(user)
    return {"status": "registered", "user_id": user.user_id, "display_name": user.display_name}


@app.post("/api/message")
async def send_message(message: IncomingMessage):
    """Send a message to an agent via the API (for testing or non-Chat clients)."""
    from src.agents.router import route_message
    message = route_message(message)
    response = await handle_message(message)
    return response.model_dump()


@app.post("/api/video/join")
async def start_video_call(request: VideoCallRequest):
    """Start a video call with a user's agent."""
    bot_name = request.bot_name or "Rentor Agent"
    session_id = await join_meeting(
        user_id=request.user_id,
        meeting_url=request.meeting_url,
        bot_name=bot_name,
    )
    if session_id:
        return {"status": "joined", "session_id": session_id}
    return {"status": "error", "message": "Failed to join meeting"}


@app.post("/api/video/leave/{user_id}")
async def end_video_call(user_id: str):
    """End an active video call."""
    success = await leave_meeting(user_id)
    return {"status": "left" if success else "error"}


def start():
    """Entry point for the application."""
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)


if __name__ == "__main__":
    start()
