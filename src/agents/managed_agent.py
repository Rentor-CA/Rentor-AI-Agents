"""Managed Agent setup and API client using Anthropic Python SDK beta namespace.

Supports: Agents, Environments, Sessions, Memory Stores, Define Outcomes,
and Multi-Agent Orchestration.
"""

import anthropic
from src.config import ANTHROPIC_API_KEY


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def create_agent(
    name: str,
    system_prompt: str,
    model: str = "claude-sonnet-4-6",
    callable_agent_ids: list[dict] | None = None,
) -> object:
    """Create a managed agent on Anthropic's cloud."""
    kwargs: dict = dict(
        name=name,
        description="Rentor property management AI agent",
        model=model,
        system=system_prompt,
        tools=[{"type": "agent_toolset_20260401"}],
    )
    if callable_agent_ids:
        kwargs["callable_agents"] = callable_agent_ids
    return _client().beta.agents.create(**kwargs)


def get_agent(agent_id: str) -> object:
    """Get an existing agent by ID."""
    return _client().beta.agents.retrieve(agent_id)


# ---------------------------------------------------------------------------
# Environments
# ---------------------------------------------------------------------------

def create_environment(name: str = "rentor-env") -> object:
    """Create a cloud environment for agent sessions."""
    return _client().beta.environments.create(
        name=name,
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )


# ---------------------------------------------------------------------------
# Memory Stores
# ---------------------------------------------------------------------------

def create_memory_store(name: str, description: str) -> object:
    """Create a memory store for persistent knowledge."""
    return _client().beta.memory_stores.create(
        name=name,
        description=description,
    )


def seed_memory(store_id: str, path: str, content: str) -> object:
    """Write a document to a memory store (upsert by path)."""
    return _client().beta.memory_stores.memories.write(
        memory_store_id=store_id,
        path=path,
        content=content,
    )


def seed_memory_store_with_policies(store_id: str, policy_text: str) -> None:
    """Split policy text into chunks and seed into a memory store.

    Individual memories are capped at 100KB. We split into ~80KB chunks
    organized by section for searchability.
    """
    max_chunk = 80_000
    if len(policy_text) <= max_chunk:
        seed_memory(store_id, "/policies/rentor-rules.md", policy_text)
        return

    # Split by major sections if possible
    sections = policy_text.split("\n\n---\n\n")
    current_chunk = ""
    chunk_idx = 1

    for section in sections:
        if len(current_chunk) + len(section) > max_chunk and current_chunk:
            seed_memory(store_id, f"/policies/rentor-rules-part-{chunk_idx}.md", current_chunk)
            chunk_idx += 1
            current_chunk = section
        else:
            current_chunk += ("\n\n---\n\n" + section) if current_chunk else section

    if current_chunk:
        seed_memory(store_id, f"/policies/rentor-rules-part-{chunk_idx}.md", current_chunk)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def create_session(
    agent_id: str,
    environment_id: str,
    memory_store_ids: list[str] | None = None,
    title: str | None = None,
) -> object:
    """Create a new session (running instance of agent + environment)."""
    kwargs: dict = dict(
        agent=agent_id,
        environment_id=environment_id,
    )
    if title:
        kwargs["title"] = title
    if memory_store_ids:
        kwargs["resources"] = [
            {
                "type": "memory_store",
                "memory_store_id": sid,
                "access": "read_write",
                "prompt": "Rentor company policies and procedures. Search this before answering policy questions.",
            }
            for sid in memory_store_ids
        ]
    return _client().beta.sessions.create(**kwargs)


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


def send_outcome(
    session_id: str,
    description: str,
    rubric: str,
    max_iterations: int = 3,
) -> None:
    """Send a Define Outcome event to a session.

    The agent will work toward the outcome, self-evaluating against the rubric.
    """
    _client().beta.sessions.events.send(
        session_id,
        events=[{
            "type": "user.define_outcome",
            "description": description,
            "rubric": {"type": "text", "content": rubric},
            "max_iterations": max_iterations,
        }],
    )


# ---------------------------------------------------------------------------
# Full Setup
# ---------------------------------------------------------------------------

def setup_rentor_agent(system_prompt: str) -> tuple[str, str]:
    """Create agent and environment. Returns (agent_id, environment_id)."""
    agent = create_agent("rentor-agent", system_prompt)
    env = create_environment()
    return agent.id, env.id


def setup_memory_store(policy_text: str) -> str:
    """Create a memory store and seed with Rentor policies. Returns store_id."""
    store = create_memory_store(
        name="rentor-policies",
        description="Rentor property management company rulebook with 573 rules covering landlords, tenants, vendors, maintenance, and company operations.",
    )
    seed_memory_store_with_policies(store.id, policy_text)
    return store.id


def setup_specialist_agents(system_prompts: dict[str, str]) -> dict[str, dict]:
    """Create specialist sub-agents for multi-agent orchestration.

    Args:
        system_prompts: Dict of {name: system_prompt} for each specialist.

    Returns:
        Dict of {name: {"id": agent_id, "version": version}}.
    """
    agents = {}
    for name, prompt in system_prompts.items():
        agent = create_agent(name, prompt)
        agents[name] = {"id": agent.id, "version": agent.version}
    return agents


def create_orchestrator_agent(
    system_prompt: str,
    callable_agents: list[dict],
) -> object:
    """Create an orchestrator agent that can delegate to specialists."""
    return create_agent(
        name="rentor-orchestrator",
        system_prompt=system_prompt,
        callable_agent_ids=[
            {"type": "agent", "id": a["id"], "version": a["version"]}
            for a in callable_agents
        ],
    )
