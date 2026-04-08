"""Routes incoming messages to the correct user's agent."""

import re
from src.models.schemas import IncomingMessage
from src.agents.agent_manager import find_user_by_name


# Patterns for cross-agent routing
_ASK_PATTERNS = [
    re.compile(r"(?:ask|talk to|message|contact)\s+(\w+(?:\s+\w+)?)'s\s+agent", re.IGNORECASE),
    re.compile(r"@(\w+(?:\s+\w+)?)'s\s+agent", re.IGNORECASE),
    re.compile(r"(?:ask|talk to)\s+(\w+(?:\s+\w+)?)\b", re.IGNORECASE),
]


def detect_target_agent(text: str) -> str | None:
    """Check if a message is directed at another user's agent.

    Returns the target user_id if found, None otherwise.
    """
    for pattern in _ASK_PATTERNS:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip()
            user = find_user_by_name(name)
            if user:
                return user.user_id
    return None


def route_message(message: IncomingMessage) -> IncomingMessage:
    """Detect cross-agent routing and update the message target.

    If the message text contains a pattern like "ask Sarah's agent about...",
    this sets the target_agent_user_id so the message goes to Sarah's agent
    instead of the sender's agent.
    """
    if message.target_agent_user_id:
        return message  # Already routed

    target = detect_target_agent(message.text)
    if target:
        message.target_agent_user_id = target

    return message
