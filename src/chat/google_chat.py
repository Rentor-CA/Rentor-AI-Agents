"""Google Chat webhook handler for incoming events.

Supports both legacy Chat app format and Workspace Add-on format
(HTTP endpoint mode sends the Add-on format with commonEventObject).
"""

from fastapi import APIRouter, Request
from src.models.schemas import IncomingMessage, MessageSource, AgentUser
from src.agents.router import route_message
from src.agents.agent_manager import handle_message_fast, get_user, register_user

router = APIRouter(prefix="/chat", tags=["google-chat"])


def _format_response(text: str, is_addon: bool = False) -> dict:
    """Format response for either legacy Chat app or Workspace Add-on format."""
    if is_addon:
        return {
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {"text": text}
                    }
                }
            }
        }
    return {"text": text}


def _normalize_event(raw: dict) -> dict:
    """Normalize Google Chat event from either legacy or Add-on format.

    HTTP endpoint mode sends Workspace Add-on format:
      {commonEventObject: {...}, authorizationEventObject: {...}, chat: {...}}

    Legacy/Pub-Sub format:
      {type: "MESSAGE", message: {...}, user: {...}, space: {...}}

    This function returns a unified format matching the legacy structure.
    """
    # If it already has 'type' at top level, it's legacy format
    if raw.get("type"):
        return raw

    # Workspace Add-on format — extract from nested 'chat' key
    chat_data = raw.get("chat", {})
    common = raw.get("commonEventObject", {})

    # The chat field may contain the full legacy event, or partial data
    if isinstance(chat_data, dict) and chat_data.get("type"):
        return chat_data

    # Try to build a legacy-style event from available data
    # Add-on format uses messagePayload inside chat
    payload = chat_data.get("messagePayload", {})
    event = {}

    # Determine event type from available signals
    if payload or "message" in chat_data or "messageText" in common:
        event["type"] = "MESSAGE"
    elif "addedToSpace" in chat_data:
        event["type"] = "ADDED_TO_SPACE"
    elif "removedFromSpace" in chat_data:
        event["type"] = "REMOVED_FROM_SPACE"
    else:
        event["type"] = "MESSAGE"

    # Extract message from messagePayload.message or fallback paths
    event["message"] = payload.get("message", chat_data.get("message", payload))
    event["user"] = chat_data.get("user", common.get("user", {}))
    event["space"] = payload.get("space", chat_data.get("space", {}))

    return event


@router.post("/webhook")
async def google_chat_webhook(request: Request):
    """Handle incoming Google Chat events."""
    raw = await request.json()
    print(f"[WEBHOOK] raw_keys={list(raw.keys())}")
    # Log chat sub-object for debugging
    chat_obj = raw.get("chat", {})
    print(f"[WEBHOOK] chat_keys={list(chat_obj.keys()) if isinstance(chat_obj, dict) else type(chat_obj)}")
    print(f"[WEBHOOK] chat={str(chat_obj)[:500]}")

    # Normalize to legacy format
    event = _normalize_event(raw)
    event_type = event.get("type", "")
    print(f"[WEBHOOK] normalized type={event_type}")
    print(f"[WEBHOOK] extracted_text='{_extract_text(raw)[:100]}'")

    # Detect if this is Add-on format (needs different response structure)
    is_addon = "commonEventObject" in raw

    if event_type == "ADDED_TO_SPACE":
        space_type = event.get("space", {}).get("type", "")
        if space_type == "DM":
            return _format_response("Hi! I'm your personal Rentor AI agent. Ask me anything about policies, procedures, or your daily work.", is_addon)
        return _format_response("Hello! I'm a Rentor AI agent. Mention me to ask questions or get help.", is_addon)

    if event_type == "REMOVED_FROM_SPACE":
        return {}

    if event_type == "MESSAGE":
        return await _handle_message_event(event, raw, is_addon)

    # Fallback: try to handle as a message if there's any text
    text = _extract_text(raw)
    if text:
        print(f"[WEBHOOK] fallback: treating as message with text='{text[:50]}'")
        return await _handle_raw_message(raw, text, is_addon)

    print(f"[WEBHOOK] unhandled event, returning empty")
    return {}


def _extract_text(raw: dict) -> str:
    """Try to extract message text from any event format."""
    # Try common paths — including Workspace Add-on messagePayload format
    for path in [
        lambda: raw.get("chat", {}).get("messagePayload", {}).get("message", {}).get("argumentText", ""),
        lambda: raw.get("chat", {}).get("messagePayload", {}).get("message", {}).get("text", ""),
        lambda: raw.get("chat", {}).get("messagePayload", {}).get("argumentText", ""),
        lambda: raw.get("chat", {}).get("messagePayload", {}).get("text", ""),
        lambda: raw.get("chat", {}).get("message", {}).get("text", ""),
        lambda: raw.get("chat", {}).get("message", {}).get("argumentText", ""),
        lambda: raw.get("commonEventObject", {}).get("parameters", {}).get("text", ""),
        lambda: raw.get("message", {}).get("text", ""),
        lambda: raw.get("message", {}).get("argumentText", ""),
    ]:
        try:
            text = path()
            if text and text.strip():
                return text.strip()
        except (AttributeError, TypeError):
            continue
    return ""


def _extract_user(raw: dict) -> dict:
    """Try to extract user info from any event format."""
    for path in [
        lambda: raw.get("chat", {}).get("user", {}),
        lambda: raw.get("chat", {}).get("messagePayload", {}).get("sender", {}),
        lambda: raw.get("user", {}),
        lambda: raw.get("commonEventObject", {}).get("user", {}),
    ]:
        try:
            user = path()
            if user and isinstance(user, dict) and user.get("name"):
                return user
        except (AttributeError, TypeError):
            continue
    return {"name": "unknown", "displayName": "Unknown"}


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


async def _handle_message_event(event: dict, raw: dict, is_addon: bool = False) -> dict:
    """Process a message event (normalized legacy format)."""
    message_data = event.get("message", {})
    sender = event.get("user", {})
    space = event.get("space", {})

    _auto_register(sender)

    text = message_data.get("argumentText", "") or message_data.get("text", "")
    text = text.strip()

    if not text:
        text = _extract_text(raw)

    if not text:
        return _format_response("I didn't catch that. Could you try again?", is_addon)

    incoming = IncomingMessage(
        source=MessageSource.GOOGLE_CHAT,
        sender_id=sender.get("name", "unknown"),
        sender_name=sender.get("displayName", "Unknown"),
        text=text,
        space_id=space.get("name"),
        thread_id=message_data.get("thread", {}).get("name"),
    )

    incoming = route_message(incoming)
    response = await handle_message_fast(incoming)

    print(f"[WEBHOOK] responding with {len(response.text)} chars, addon={is_addon}")
    return _format_response(response.text, is_addon)


async def _handle_raw_message(raw: dict, text: str, is_addon: bool = False) -> dict:
    """Handle a message extracted directly from raw event data."""
    sender = _extract_user(raw)
    _auto_register(sender)

    incoming = IncomingMessage(
        source=MessageSource.GOOGLE_CHAT,
        sender_id=sender.get("name", "unknown"),
        sender_name=sender.get("displayName", "Unknown"),
        text=text,
    )

    incoming = route_message(incoming)
    response = await handle_message_fast(incoming)

    print(f"[WEBHOOK] fallback responding with {len(response.text)} chars, addon={is_addon}")
    return _format_response(response.text, is_addon)
