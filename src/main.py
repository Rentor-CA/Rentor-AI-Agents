"""FastAPI application entry point for Rentor AI Agents (Managed Agents).

Features: Memory Stores, Define Outcomes, Multi-Agent Orchestration.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import (
    PORT, MANAGED_AGENT_ID, MANAGED_ENVIRONMENT_ID, MANAGED_MEMORY_STORE_ID,
)
from src.chat.google_chat import router as chat_router
from src.agents.agent_manager import register_user, handle_message, configure
from src.agents.managed_agent import (
    get_agent, setup_rentor_agent, setup_memory_store,
    setup_specialist_agents, create_orchestrator_agent,
)
from src.agents.system_prompts import build_base_prompt
from src.knowledge.policy_loader import load_all_policies
from src.models.schemas import AgentUser, IncomingMessage, MessageSource, VideoCallRequest
from src.video.pika_manager import join_meeting, leave_meeting


# Specialist agent system prompts for multi-agent orchestration
SPECIALIST_PROMPTS = {
    "rentor-leasing-agent": (
        "You are the Rentor Leasing Specialist. You handle all questions about "
        "tenant screening, lease applications, rental criteria, showings, move-ins, "
        "lease renewals, and tenant onboarding. You know the RAF scoring system, "
        "DLAR tracking, and Appfolio leasing workflows."
    ),
    "rentor-maintenance-agent": (
        "You are the Rentor Maintenance Specialist. You handle all questions about "
        "work orders, vendor management, emergency maintenance, routine repairs, "
        "property inspections, turnover processes, and the WOOO protocol. "
        "You know Appfolio work order workflows and vendor payment schedules."
    ),
    "rentor-compliance-agent": (
        "You are the Rentor Compliance Specialist. You handle all questions about "
        "California landlord-tenant law, fair housing, habitability requirements, "
        "lead paint, mold remediation, security deposits, eviction procedures, "
        "insurance requirements, and DRE compliance."
    ),
}

ORCHESTRATOR_PROMPT = """You are the Rentor AI Manager, the primary AI agent for Rentor property management.

Your role:
- Answer general questions about Rentor policies and procedures directly
- Delegate specialized questions to your specialist agents:
  - Leasing Specialist: tenant screening, applications, showings, move-ins, renewals
  - Maintenance Specialist: work orders, vendors, repairs, inspections, turnovers
  - Compliance Specialist: California law, fair housing, habitability, evictions, insurance
- Coordinate between specialists when a question spans multiple areas
- Always be professional, concise, and helpful

When a team member asks a question, decide whether to answer directly or delegate.
For complex questions, you may consult multiple specialists and synthesize their answers."""


def _init_managed_agent() -> tuple[str, str, str]:
    """Initialize or reuse the managed agent, environment, and memory store."""
    agent_id = MANAGED_AGENT_ID
    env_id = MANAGED_ENVIRONMENT_ID
    store_id = MANAGED_MEMORY_STORE_ID

    # If all IDs are set, try to reuse them
    if agent_id and env_id:
        try:
            get_agent(agent_id)
            print(f"Reusing existing managed agent: {agent_id}")
            return agent_id, env_id, store_id
        except Exception:
            print("Stored agent IDs invalid, creating new ones...")

    # --- Step 1: Create specialist agents ---
    print("Creating specialist agents...")
    try:
        specialists = setup_specialist_agents(SPECIALIST_PROMPTS)
        specialist_list = list(specialists.values())
        print(f"  Created {len(specialists)} specialists: {list(specialists.keys())}")
    except Exception as e:
        print(f"  Specialist agents failed (research preview): {e}")
        specialist_list = []

    # --- Step 2: Create orchestrator (or simple agent if multi-agent unavailable) ---
    print("Creating orchestrator agent...")
    try:
        if specialist_list:
            agent = create_orchestrator_agent(ORCHESTRATOR_PROMPT, specialist_list)
        else:
            # Fallback: simple agent with knowledge in system prompt
            system_prompt = build_base_prompt("{user}", "Team Member", "Operations")
            agent_id_new, env_id_new = setup_rentor_agent(system_prompt)
            agent_id = agent_id_new
    except Exception:
        system_prompt = build_base_prompt("{user}", "Team Member", "Operations")
        agent_id_new, env_id_new = setup_rentor_agent(system_prompt)
        agent_id = agent_id_new

    if not agent_id:
        agent_id = agent.id

    # --- Step 3: Create environment ---
    if not env_id:
        from src.agents.managed_agent import create_environment
        env = create_environment()
        env_id = env.id

    # --- Step 4: Create memory store and seed with policies ---
    print("Creating memory store...")
    try:
        policy_text = load_all_policies()
        if policy_text:
            store_id = setup_memory_store(policy_text)
            print(f"  Memory store seeded with {len(policy_text)} chars of policies")
        else:
            print("  No policies found to seed")
            store_id = ""
    except Exception as e:
        print(f"  Memory store failed (research preview): {e}")
        store_id = ""

    print(f"Managed Agent setup complete!")
    print(f"  MANAGED_AGENT_ID={agent_id}")
    print(f"  MANAGED_ENVIRONMENT_ID={env_id}")
    print(f"  MANAGED_MEMORY_STORE_ID={store_id}")
    print("Add these to your .env to reuse on restart.")

    return agent_id, env_id, store_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    print("Rentor AI Agents (Managed) starting up...")

    try:
        agent_id, env_id, store_id = _init_managed_agent()
        memory_ids = [store_id] if store_id else []
        configure(agent_id, env_id, memory_ids)
        print("Managed agent configured and ready.")
    except Exception as e:
        print(f"WARNING: Could not initialize managed agent: {e}")
        print("The server will start but agent messages will fail.")

    yield
    print("Rentor AI Agents shutting down.")


app = FastAPI(
    title="Rentor AI Agents",
    description="Personal AI agents for Rentor property management team (powered by Claude Managed Agents)",
    version="0.3.0",
    lifespan=lifespan,
)

# Mount Google Chat webhook router
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Rentor AI Agents",
        "version": "0.3.0",
        "platform": "Claude Managed Agents",
        "features": [
            "Memory Stores (persistent knowledge base)",
            "Define Outcomes (self-evaluation)",
            "Multi-Agent Orchestration (specialist delegation)",
            "Google Chat integration",
            "Pika video calls",
        ],
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
    return {"status": "ok", "service": "rentor-ai-agents", "version": "0.3.0"}


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
