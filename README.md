# Rentor AI Agents

Personal AI agents for the Rentor property management team. Each team member gets their own AI agent that can:

- Chat via Google Chat (DMs and spaces)
- Answer questions about company policies and procedures
- Collaborate on daily work tasks
- Be contacted by other team members on your behalf
- Join video calls via Pika for face-to-face collaboration

## Quick Start

### Prerequisites
- Python 3.10+
- [Anthropic API key](https://console.anthropic.com/)
- [Pika Developer key](https://www.pika.me/dev/) (for video calls)
- Google Workspace admin access (for Google Chat integration)

### Setup

1. Clone and install:
```bash
git clone https://github.com/Rentor-CA/Rentor-AI-Agents.git
cd Rentor-AI-Agents
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Add company policies to `knowledge_base/` (markdown or text files).

4. Run the server:
```bash
python -m src.main
```

The API will be available at `http://localhost:8080`.

### Docker

```bash
docker compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat/webhook` | POST | Google Chat webhook (configured in Google Cloud) |
| `/api/users` | POST | Register a team member |
| `/api/message` | POST | Send a message to an agent |
| `/api/video/join` | POST | Start a video call with an agent |
| `/api/video/leave/{user_id}` | POST | End a video call |

## Architecture

- **FastAPI** server handles Google Chat webhooks and API requests
- **Claude API** powers each agent's intelligence
- **Per-user agents** with personalized system prompts and company knowledge
- **Cross-agent routing** lets team members talk to each other's agents
- **Pika-Skills** enables live video call participation

## Project Structure

```
src/
  main.py              # FastAPI app entry point
  config.py            # Environment & settings
  agents/              # Agent management & routing
  chat/                # Google Chat integration
  video/               # Pika video call integration
  knowledge/           # Policy document loader
  models/              # Pydantic schemas
skills/                # Pika-Skills (video meeting)
knowledge_base/        # Company policy documents
tests/                 # Test suite
```
