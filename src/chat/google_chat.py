"""Google Chat webhook handler for incoming events."""

from fastapi import APIRouter, Request, HTTPException
from src.models.schemas import IncomingMessage, MessageSource, AgentUser
from src.agents.router import route_message
from src.agents.agent_manager import handle_message_fast, get_user, register_user

router = APIRouter(prefix="/chat", tags=["google-chat"])


@router.post("/webhook")
async def google_chat_webhook(request: Request):
    """Handle incoming Google Chat events.

    Google Chat sends POST requests for:
    - MESSAGE: User sent a message
    - ADDED_TO_SPACE: Bot was added to a space or DM
    - REMOVED_FROM_SPACE: Bot was removed
    - CARD_CLICKED: User clicked a card button
    """
    event = await request.json()
    event_type = event.get("type", "")
    print(f"[WEBHOOK] type={event_type} user={event.get('user', {}).get('displayName', '?')}")

    if event_type == "ADDED_TO_SPACE":
        space_type = event.get("space", {}).get("type", "")
        if space_type == "DM":
            return {"text": "Hi! I'm your personal Rentor AI agent. Ask me anything about policies, procedures, or your daily work."}
        return {"text": "Hello! I'm a Rentor AI agent. Mention me to ask questions or get help."}

    if event_type == "REMOVED_FROM_SPACE":
        return {}

    if event_type == "MESSAGE":
        return await _handle_message_event(event)

    if event_type == "CARD_CLICKED":
        return await _handle_card_click(event)

    return {}


def _auto_register(sender: dict) -> None:
    """Auto-register a Google Chat user if not already registered."""
    user_id = sender.get("name", "unknown")
    if get_user(user_id):
        return

    display_name = sender.get("displayName", "Unknown")
    email = sender.get("email", "")

    register_user(AgentUser(
        user_id=user_id,
        display_name=display_name,
        email=email,
        role="Team Member",
        department="Operations",
    ))


async def _handle_message_event(event: dict) -> dict:
    """Process an incoming message event from Google Chat."""
    message_data = event.get("message", {})
    sender = event.get("user", {})
    space = event.get("space", {})

    # Auto-register the sender if they're new
    _auto_register(sender)

    text = message_data.get("argumentText", "") or message_data.get("text", "")
    text = text.strip()

    if not text:
        return {"text": "I didn't catch that. Could you try again?"}

    incoming = IncomingMessage(
        source=MessageSource.GOOGLE_CHAT,
        sender_id=sender.get("name", "unknown"),
        sender_name=sender.get("displayName", "Unknown"),
        text=text,
        space_id=space.get("name"),
        thread_id=message_data.get("thread", {}).get("name"),
    )

    # Check for cross-agent routing
    incoming = route_message(incoming)

    # Get response using fast sync handler (Google Chat has 30s timeout)
    response = await handle_message_fast(incoming)

    result: dict = {"text": response.text}
    print(f"[WEBHOOK] responding with {len(response.text)} chars")

    # Thread the response if in a space
    thread_name = message_data.get("thread", {}).get("name")
    if thread_name:
        result["thread"] = {"name": thread_name}

    return result


async def _handle_card_click(event: dict) -> dict:
    """Handle interactive card button clicks."""
    action = event.get("action", {})
    action_name = action.get("actionMethodName", "")

    if action_name == "start_video_call":
        params = action.get("parameters", [])
        meeting_url = next(
            (p["value"] for p in params if p["key"] == "meeting_url"), None
        )
        if meeting_url:
            return {"text": f"Starting video call... Join at: {meeting_url}"}

    return {"text": "Action received."}
