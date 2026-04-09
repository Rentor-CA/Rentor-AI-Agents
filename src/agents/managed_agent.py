"""Managed Agent setup and API client using Anthropic Python SDK beta namespace."""

import anthropic
from src.config import ANTHROPIC_API_KEY


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def create_agent(name: str, system_prompt: str, model: str = "claude-sonnet-4-6") -> object:
    """Create a managed agent on Anthropic's cloud."""
    return _client().beta.agents.create(
        name=name,
        description="Rentor property management AI agent",
        model=model,
        system=system_prompt,
        tools=[{"type": "agent_toolset_20260401"}],
    )


def get_agent(agent_id: str) -> object:
    """Get an existing agent by ID."""
    return _client().beta.agents.retrieve(agent_id)


def create_environment(name: str = "rentor-env") -> object:
    """Create a cloud environment for agent sessions."""
    return _client().beta.environments.create(
        name=name,
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )


def create_session(agent_id: str, environment_id: str) -> object:
    """Create a new session (running instance of agent + environment)."""
    return _client().beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
    )


def send_message(session_id: str, content: str) -> str:
    """Send a message to a session and collect the full response.

    Opens a stream, sends the user message, then collects agent messages
    until the session goes idle.
    """
    client = _client()
    response_parts: list[str] = []

    with client.beta.sessions.events.stream(session_id) as stream:
        # Send the user message after the stream opens
        client.beta.sessions.events.send(
            session_id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": content}],
            }],
        )

        # Process streaming events
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if hasattr(block, "text"):
                        response_parts.append(block.text)
            elif event.type == "session.status_idle":
                break
            elif event.type == "session.error":
                error_msg = getattr(event, "error", "Unknown error")
                response_parts.append(f"[Agent error: {error_msg}]")
                break

    return "".join(response_parts) if response_parts else "I couldn't generate a response."


def setup_rentor_agent(system_prompt: str) -> tuple[str, str]:
    """One-shot setup: create agent and environment.

    Returns (agent_id, environment_id).
    """
    agent = create_agent("rentor-agent", system_prompt)
    env = create_environment()
    return agent.id, env.id
