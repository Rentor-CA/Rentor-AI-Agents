"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent

load_dotenv(PROJECT_ROOT / ".env", override=True)
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
SKILLS_DIR = PROJECT_ROOT / "skills"
AGENT_SESSIONS_DIR = PROJECT_ROOT / "agent_sessions"

# Ensure session directory exists
AGENT_SESSIONS_DIR.mkdir(exist_ok=True)

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
PIKA_DEV_KEY = os.getenv("PIKA_DEV_KEY", "")

# Google Chat
GOOGLE_CHAT_PROJECT_ID = os.getenv("GOOGLE_CHAT_PROJECT_ID", "")
GOOGLE_CHAT_SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_CHAT_SERVICE_ACCOUNT_PATH", "./service-account.json"
)

# Server
PORT = int(os.getenv("PORT", "8080"))

# Agent defaults
DEFAULT_MODEL = "claude-sonnet-4-6"
COMPANY_NAME = "Rentor"

# Managed Agent IDs (set after first setup, reused on restart)
MANAGED_AGENT_ID = os.getenv("MANAGED_AGENT_ID", "")
MANAGED_ENVIRONMENT_ID = os.getenv("MANAGED_ENVIRONMENT_ID", "")
MANAGED_MEMORY_STORE_ID = os.getenv("MANAGED_MEMORY_STORE_ID", "")
