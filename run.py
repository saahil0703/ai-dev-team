#!/usr/bin/env python3
"""
AI Dev Team Platform — Main Entry Point
Starts the dashboard and provides CLI for triggering sprints/meetings.
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

def start_server():
    """Start the dashboard server"""
    import uvicorn
    port = int(os.getenv("PORT", 8502))
    print(f"🚀 AI Dev Team Platform starting on http://localhost:{port}")
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=port, log_level="info", reload=os.getenv("DEBUG", "false").lower() == "true")

async def run_sprint(sprint_number: int, goals: list):
    """Run a sprint with the AI team"""
    from agents.orchestrator import Orchestrator
    project_dir = Path(__file__).parent
    orchestrator = Orchestrator(project_dir)
    result = await orchestrator.run_sprint(sprint_number, goals)
    print(f"\n✅ Sprint {sprint_number} complete!")
    print(f"   Tasks completed: {result['tasks_completed']}")
    print(f"   Bugs found: {result['bugs_found']}")
    return result

async def run_meeting(topic: str, participants: list = None):
    """Run an ad-hoc meeting"""
    from agents.orchestrator import Orchestrator
    project_dir = Path(__file__).parent
    orchestrator = Orchestrator(project_dir)
    participants = participants or ["architect", "frontend", "backend", "qa"]
    result = await orchestrator.run_ad_hoc_meeting(topic, participants)
    print(f"\n✅ Meeting complete: {result.get('transcript_file', 'saved')}")
    return result

def main():
    parser = argparse.ArgumentParser(description="AI Dev Team Platform")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # Server
    sub.add_parser("server", help="Start the dashboard server")

    # Sprint
    sp = sub.add_parser("sprint", help="Run a sprint")
    sp.add_argument("number", type=int, help="Sprint number")
    sp.add_argument("--goals", nargs="+", required=True, help="Sprint goals")

    # Meeting
    mp = sub.add_parser("meeting", help="Run an ad-hoc meeting")
    mp.add_argument("topic", help="Meeting topic")
    mp.add_argument("--participants", nargs="+", default=None)

    args = parser.parse_args()

    if args.command == "server" or args.command is None:
        start_server()
    elif args.command == "sprint":
        asyncio.run(run_sprint(args.number, args.goals))
    elif args.command == "meeting":
        asyncio.run(run_meeting(args.topic, args.participants))

if __name__ == "__main__":
    main()
