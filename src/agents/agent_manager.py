"""Manages per-user Claude agents with persistent sessions via Managed Agents API.

Supports Memory Stores for knowledge base and Multi-Agent orchestration.
"""

import anthropic
from src.agents.managed_agent import create_session, send_message
from src.config import ANTHROPIC_API_KEY, DEFAULT_MODEL
from src.agents.system_prompts import build_full_prompt
from src.knowledge.policy_loader import load_all_policies
from src.models.schemas import AgentUser, IncomingMessage, AgentResponse

# In-memory registry of user agents and their sessions
_user_registry: dict[str, AgentUser] = {}
_user_sessions: dict[str, str] = {}  # user_id -> session_id

# Set by main.py on startup
_agent_id: str = ""
_environment_id: str = ""
_memory_store_ids: list[str] = []


def configure(
    agent_id: str,
    environment_id: str,
    memory_store_ids: list[str] | None = None,
) -> None:
    """Configure the global managed agent IDs. Called once at startup."""
    global _agent_id, _environment_id, _memory_store_ids
    _agent_id = agent_id
    _environment_id = environment_id
    _memory_store_ids = memory_store_ids or []


def register_user(user: AgentUser) -> None:
    """Register a team member to get a personal agent."""
    _user_registry[user.user_id] = user


def get_user(user_id: str) -> AgentUser | None:
    """Look up a registered user."""
    return _user_registry.get(user_id)


def get_all_users() -> list[AgentUser]:
    """List all registered users."""
    return list(_user_registry.values())


def find_user_by_name(name: str) -> AgentUser | None:
    """Find a user by display name (case-insensitive partial match)."""
    name_lower = name.lower()
    for user in _user_registry.values():
        if name_lower in user.display_name.lower():
            return user
    return None


def _get_or_create_session(user_id: str) -> str:
    """Get existing session or create a new one for this user."""
    if user_id in _user_sessions:
        return _user_sessions[user_id]

    user = get_user(user_id)
    title = f"{user.display_name}'s session" if user else f"Session for {user_id}"

    session = create_session(
        agent_id=_agent_id,
        environment_id=_environment_id,
        memory_store_ids=_memory_store_ids if _memory_store_ids else None,
        title=title,
    )
    session_id = session.id
    _user_sessions[user_id] = session_id
    return session_id


async def handle_message(message: IncomingMessage) -> AgentResponse:
    """Process a message through the appropriate user's managed agent session."""

    target_user_id = message.target_agent_user_id or message.sender_id
    user = get_user(target_user_id)

    if not user:
        return AgentResponse(
            text="No agent is registered for this user. Please contact an admin to set up your personal agent.",
            agent_user_id=target_user_id,
            agent_display_name="System",
        )

    # Build the message with sender context
    user_message = message.text
    if message.sender_id != target_user_id:
        sender = get_user(message.sender_id)
        sender_name = sender.display_name if sender else message.sender_name
        user_message = f"[Message from team member {sender_name}]: {message.text}"

    # Get or create a persistent session for this user
    session_id = _get_or_create_session(target_user_id)

    # Send to managed agent session and get response
    try:
        response_text = send_message(session_id, user_message)
    except Exception:
        # Session may have expired — create a new one and retry
        _user_sessions.pop(target_user_id, None)
        session_id = _get_or_create_session(target_user_id)
        try:
            response_text = send_message(session_id, user_message)
        except Exception as retry_err:
            response_text = f"I'm having trouble connecting right now. Error: {retry_err}"

    return AgentResponse(
        text=response_text,
        agent_user_id=user.user_id,
        agent_display_name=f"{user.display_name}'s Agent",
    )


# Cache the system prompt so we don't rebuild it every call
_cached_system_prompt: str = ""


_cached_system_prompt: str = ""


def _get_system_prompt(user: AgentUser) -> str:
    """Get system prompt with knowledge base, kept short for fast responses."""
    global _cached_system_prompt
    if not _cached_system_prompt:
        policy_text = load_all_policies()
        # Keep prompt under 30K chars for fast Google Chat responses
        max_chars = 25_000
        if len(policy_text) > max_chars:
            policy_text = policy_text[:max_chars] + "\n\n[... See full rulebook for remaining rules ...]"
        _cached_system_prompt = build_full_prompt(
            user_name=user.display_name,
            user_role=user.role,
            user_department=user.department,
            policy_text=policy_text,
        )
    return _cached_system_prompt


async def handle_message_fast(message: IncomingMessage) -> AgentResponse:
    """Fast handler using Claude Messages API for Google Chat (30s timeout)."""
    target_user_id = message.target_agent_user_id or message.sender_id
    user = get_user(target_user_id)

    if not user:
        return AgentResponse(
            text="Hi! I'm your Rentor AI agent. I'm ready to help with policies and procedures.",
            agent_user_id=target_user_id,
            agent_display_name="Rentor Agent",
        )

    system_prompt = _get_system_prompt(user)

    user_message = message.text
    if message.sender_id != target_user_id:
        sender = get_user(message.sender_id)
        sender_name = sender.display_name if sender else message.sender_name
        user_message = f"[Message from team member {sender_name}]: {message.text}"

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast model for Google Chat
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = response.content[0].text if response.content else "I couldn't generate a response."
    except Exception as e:
        response_text = f"I'm having trouble right now. Error: {e}"

    return AgentResponse(
        text=response_text,
        agent_user_id=user.user_id,
        agent_display_name=f"{user.display_name}'s Agent",
    )
