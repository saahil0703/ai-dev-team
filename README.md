# 🤖 AI Dev Team Platform

A standalone AI-powered software development team. Agents design, code, review, and ship — you watch it all happen live on a cyberpunk mission control dashboard.

## Features

- **4 AI Agents** — Architect (Alex), Frontend (Frankie), Backend (Blake), QA (Quinn)
- **Real Meetings** — Agents debate, disagree, and reach consensus. Watch live via Meeting Spy.
- **Sprint Orchestration** — Plan → Design → Code → Review → Ship
- **Live Dashboard** — Kanban board, agent status, burndown charts, activity feed
- **QA Veto Power** — Quinn can block releases if quality isn't met
- **Invite-Code Auth** — Share access without exposing API keys

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USER/ai-dev-team.git
cd ai-dev-team

# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

# Run
python run.py
```

Open **http://localhost:8502** → enter an invite code → you're in.

## Deploy to Railway

1. Push to GitHub
2. Connect repo on [Railway](https://railway.app)
3. Add environment variables (copy from `.env.example`)
4. Deploy — Railway auto-detects the Dockerfile

## Usage

### Dashboard (default)
```bash
python run.py              # Start dashboard on port 8502
python run.py server       # Same thing
```

### Run a Sprint (CLI)
```bash
python run.py sprint 1 --goals "Build user auth" "Create transaction API" "Design dashboard UI"
```

### Run a Meeting (CLI)
```bash
python run.py meeting "Sprint 2 Planning" --participants architect frontend backend qa
```

### Trigger from Dashboard
Click **🚀 Start Sprint** or **📋 New Meeting** buttons in the dashboard header.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Your Anthropic API key |
| `AGENT_MODEL` | — | `claude-sonnet-4-20250514` | Default model for all agents |
| `ARCHITECT_MODEL` | — | `AGENT_MODEL` | Override model for architect |
| `FRONTEND_MODEL` | — | `AGENT_MODEL` | Override model for frontend |
| `BACKEND_MODEL` | — | `AGENT_MODEL` | Override model for backend |
| `QA_MODEL` | — | `AGENT_MODEL` | Override model for QA |
| `INVITE_CODES` | — | `alpha,beta,gamma,dev-team,demo` | Comma-separated invite codes |
| `PORT` | — | `8502` | Dashboard port |
| `DEBUG` | — | `false` | Enable hot reload |

## Architecture

```
User → Dashboard (FastAPI) → Orchestrator → Agents (Anthropic API)
                 ↕                              ↕
              Browser ←── SSE ←── live-meeting.jsonl
                 ↕
            state.json (kanban, metrics, activity)
```

## License

MIT
