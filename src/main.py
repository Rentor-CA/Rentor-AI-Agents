"""FastAPI application entry point for Rentor AI Agents (Managed Agents)."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import (
    PORT, MANAGED_AGENT_ID, MANAGED_ENVIRONMENT_ID, MANAGED_MEMORY_STORE_ID,
)
from src.chat.google_chat import router as chat_router
from src.agents.agent_manager import register_user, handle_message, configure
from src.agents.managed_agent import setup_rentor_agent, get_agent
from src.agents.system_prompts import build_base_prompt
from src.models.schemas import AgentUser, IncomingMessage, MessageSource, VideoCallRequest
from src.video.pika_manager import join_meeting, leave_meeting


def _init_managed_agent() -> tuple[str, str]:
    """Initialize or reuse the managed agent and environment."""
    agent_id = MANAGED_AGENT_ID
    env_id = MANAGED_ENVIRONMENT_ID

    # If IDs are set, try to reuse them
    if agent_id and env_id:
        try:
            get_agent(agent_id)
            print(f"Reusing existing managed agent: {agent_id}")
            return agent_id, env_id
        except Exception:
            print("Stored agent IDs invalid, creating new ones...")

    # Create new agent and environment with knowledge base
    print("Setting up new managed agent...")
    from src.knowledge.policy_loader import load_all_policies
    from src.agents.system_prompts import build_full_prompt
    policy_text = load_all_policies()
    # Managed Agents has a 100K char limit on system prompt.
    # Truncate policy text if needed, keeping the most important rules.
    max_policy_chars = 80_000
    if len(policy_text) > max_policy_chars:
        policy_text = policy_text[:max_policy_chars] + "\n\n[... Additional rules truncated for length ...]"
    system_prompt = build_full_prompt(
        user_name="{user}",
        user_role="Team Member",
        user_department="Operations",
        policy_text=policy_text,
    )
    agent_id, env_id = setup_rentor_agent(system_prompt)

    print(f"Managed Agent created!")
    print(f"  MANAGED_AGENT_ID={agent_id}")
    print(f"  MANAGED_ENVIRONMENT_ID={env_id}")
    print("Add these to your .env to reuse on restart.")

    return agent_id, env_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    print("Rentor AI Agents (Managed) starting up...")

    try:
        agent_id, env_id = _init_managed_agent()
        configure(agent_id, env_id)
        print("Managed agent configured and ready.")
    except Exception as e:
        print(f"WARNING: Could not initialize managed agent: {e}")
        print("The server will start but agent messages will fail.")

    yield
    print("Rentor AI Agents shutting down.")


app = FastAPI(
    title="Rentor AI Agents",
    description="Personal AI agents for Rentor property management team (powered by Claude Managed Agents)",
    version="0.2.0",
    lifespan=lifespan,
)

# Mount Google Chat webhook router
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Rentor AI Agents",
        "version": "0.2.0",
        "platform": "Claude Managed Agents",
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
    return {"status": "ok", "service": "rentor-ai-agents", "platform": "managed-agents"}


@app.post("/api/users")
async def create_user(user: AgentUser):
    """Register a new team member with a personal agent."""
    register_user(user)
    return {"status": "registered", "user_id": user.user_id, "display_name": user.display_name}


@app.post("/api/message")
async def send_message_endpoint(message: IncomingMessage):
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
