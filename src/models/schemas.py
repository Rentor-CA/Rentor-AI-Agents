"""Pydantic models for requests and responses."""

from pydantic import BaseModel
from enum import Enum


class AgentUser(BaseModel):
    """A registered team member with a personal agent."""
    user_id: str
    display_name: str
    email: str
    role: str = ""
    department: str = ""
    avatar_path: str | None = None
    voice_id: str | None = None


class MessageSource(str, Enum):
    GOOGLE_CHAT = "google_chat"
    API = "api"
    VIDEO_CALL = "video_call"


class IncomingMessage(BaseModel):
    """A message received from any source."""
    source: MessageSource
    sender_id: str
    sender_name: str
    text: str
    space_id: str | None = None
    thread_id: str | None = None
    target_agent_user_id: str | None = None  # For "ask {person}'s agent"


class AgentResponse(BaseModel):
    """Response from an agent."""
    text: str
    agent_user_id: str
    agent_display_name: str
    cards: list[dict] | None = None  # Google Chat card payloads


class VideoCallRequest(BaseModel):
    """Request to start a video call with an agent."""
    user_id: str
    meeting_url: str
    bot_name: str | None = None
