"""Manages per-user Claude agents with persistent sessions."""

import anthropic
from src.config import ANTHROPIC_API_KEY, DEFAULT_MODEL, MAX_AGENT_TURNS
from src.agents.system_prompts import build_full_prompt
from src.knowledge.policy_loader import load_all_policies
from src.models.schemas import AgentUser, IncomingMessage, AgentResponse


# In-memory registry of user agents
_user_registry: dict[str, AgentUser] = {}


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


async def handle_message(message: IncomingMessage) -> AgentResponse:
    """Process a message through the appropriate user's agent."""

    # Determine which agent should respond
    target_user_id = message.target_agent_user_id or message.sender_id
    user = get_user(target_user_id)

    if not user:
        return AgentResponse(
            text=f"No agent is registered for this user. Please contact an admin to set up your personal agent.",
            agent_user_id=target_user_id,
            agent_display_name="System",
        )

    # Build system prompt with knowledge base
    policy_text = load_all_policies()
    system_prompt = build_full_prompt(
        user_name=user.display_name,
        user_role=user.role,
        user_department=user.department,
        policy_text=policy_text,
    )

    # Call Claude API
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Add context about who is asking
    sender_context = ""
    if message.sender_id != target_user_id:
        sender = get_user(message.sender_id)
        sender_name = sender.display_name if sender else message.sender_name
        sender_context = f"[Message from team member {sender_name}]: "

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": sender_context + message.text}
        ],
    )

    response_text = response.content[0].text if response.content else "I couldn't generate a response."

    return AgentResponse(
        text=response_text,
        agent_user_id=user.user_id,
        agent_display_name=f"{user.display_name}'s Agent",
    )
