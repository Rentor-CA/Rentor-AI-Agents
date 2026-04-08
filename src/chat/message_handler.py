"""Message processing utilities for incoming chat messages."""

import re

# Pattern to detect video call requests
VIDEO_CALL_PATTERN = re.compile(
    r"(?:start|join|begin|schedule)\s+(?:a\s+)?(?:video\s+)?call",
    re.IGNORECASE,
)

# Pattern to detect meeting URLs
MEETING_URL_PATTERN = re.compile(
    r"(https?://(?:meet\.google\.com|zoom\.us|[a-z]+\.zoom\.us)/\S+)",
    re.IGNORECASE,
)


def is_video_call_request(text: str) -> bool:
    """Check if the message is requesting a video call."""
    return bool(VIDEO_CALL_PATTERN.search(text))


def extract_meeting_url(text: str) -> str | None:
    """Extract a Google Meet or Zoom URL from the message text."""
    match = MEETING_URL_PATTERN.search(text)
    return match.group(1) if match else None


def clean_message_text(text: str) -> str:
    """Remove bot mentions and clean up message text."""
    # Remove @mentions
    text = re.sub(r"<users/\d+>", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
