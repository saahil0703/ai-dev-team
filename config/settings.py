"""
Configuration settings for the AI Dev Team Platform
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Project Configuration
PROJECT_NAME = os.getenv("PROJECT_NAME", "AI Dev Team Platform")
PROJECT_DESCRIPTION = os.getenv("PROJECT_DESCRIPTION", "Standalone AI development team with real-time collaboration")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
PORT = int(os.getenv("PORT", "8502"))

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("⚠️  ANTHROPIC_API_KEY not set — agents won't work until configured. Dashboard still runs.")

# Authentication
INVITE_CODES = os.getenv("INVITE_CODES", "demo,alpha,beta").split(",")
SESSION_SECRET = os.getenv("SESSION_SECRET", "ai-dev-team-platform-secret-key-change-me-in-production")

# File Paths
BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
MEETINGS_DIR = BASE_DIR / "meetings"
DOCS_DIR = BASE_DIR / "docs"

# Create directories if they don't exist
STATE_DIR.mkdir(exist_ok=True)
MEETINGS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# Create .gitkeep files
for dir_path in [STATE_DIR, MEETINGS_DIR, DOCS_DIR]:
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()