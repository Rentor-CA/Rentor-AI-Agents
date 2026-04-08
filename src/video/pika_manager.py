"""Pika video call integration for live AI agent meetings."""

import subprocess
import sys
from pathlib import Path
from src.config import PIKA_DEV_KEY, SKILLS_DIR, AGENT_SESSIONS_DIR

PIKA_SCRIPT = SKILLS_DIR / "pikastream-video-meeting" / "scripts" / "pikastreaming_videomeeting.py"

# Store active video sessions
_active_sessions: dict[str, str] = {}  # user_id -> session_id


def _run_pika_command(args: list[str]) -> tuple[str, int]:
    """Run a Pika script command and return (output, return_code)."""
    env = {"PIKA_DEV_KEY": PIKA_DEV_KEY}
    cmd = [sys.executable, str(PIKA_SCRIPT)] + args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, **env},
        timeout=120,
    )
    output = result.stdout + result.stderr
    return output.strip(), result.returncode


def generate_avatar(user_id: str, output_path: Path | None = None) -> str | None:
    """Generate an avatar image for a user's agent.

    Returns the path to the generated avatar, or None on failure.
    """
    if output_path is None:
        output_path = AGENT_SESSIONS_DIR / f"{user_id}_avatar.png"

    output, code = _run_pika_command([
        "generate-avatar",
        "--output", str(output_path),
    ])

    if code == 0 and output_path.exists():
        return str(output_path)
    return None


def clone_voice(audio_path: str, voice_name: str) -> str | None:
    """Clone a voice from an audio sample.

    Returns the voice_id on success, or None on failure.
    """
    output, code = _run_pika_command([
        "clone-voice",
        "--audio", audio_path,
        "--name", voice_name,
        "--noise-reduction",
    ])

    if code == 0:
        # Parse voice_id from output
        for line in output.splitlines():
            if "voice_id" in line.lower() or "voice id" in line.lower():
                parts = line.split(":")
                if len(parts) >= 2:
                    return parts[-1].strip()
        return output.strip()  # Return full output as fallback
    return None


async def join_meeting(
    user_id: str,
    meeting_url: str,
    bot_name: str,
    avatar_path: str | None = None,
    system_prompt: str = "",
    voice_id: str | None = None,
) -> str | None:
    """Join a video meeting as an AI agent.

    Returns the session_id on success, or None on failure.
    """
    args = [
        "join",
        "--meet-url", meeting_url,
        "--bot-name", bot_name,
    ]

    if avatar_path:
        args.extend(["--image", avatar_path])

    if system_prompt:
        # Write system prompt to temp file
        prompt_path = AGENT_SESSIONS_DIR / f"{user_id}_meeting_prompt.txt"
        prompt_path.write_text(system_prompt, encoding="utf-8")
        args.extend(["--system-prompt-file", str(prompt_path)])

    if voice_id:
        args.extend(["--voice-id", voice_id])

    output, code = _run_pika_command(args)

    if code == 0:
        # Parse session_id from output
        for line in output.splitlines():
            if "session" in line.lower():
                parts = line.split(":")
                if len(parts) >= 2:
                    session_id = parts[-1].strip()
                    _active_sessions[user_id] = session_id
                    return session_id
        return output.strip()
    return None


async def leave_meeting(user_id: str) -> bool:
    """Leave an active video meeting."""
    session_id = _active_sessions.get(user_id)
    if not session_id:
        return False

    output, code = _run_pika_command([
        "leave",
        "--session-id", session_id,
    ])

    if code == 0:
        _active_sessions.pop(user_id, None)
        return True
    return False


def get_active_session(user_id: str) -> str | None:
    """Get the active video session for a user, if any."""
    return _active_sessions.get(user_id)
