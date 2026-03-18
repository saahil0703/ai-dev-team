#!/usr/bin/env python3
"""
PROFIT TRACKER - Real-Time AI Team Dashboard
Premium Mission Control Interface

To run:
1. cd /Users/saa/.openclaw/workspace/profit-tracker/dashboard
2. python3 -m venv venv && source venv/bin/activate
3. pip install fastapi uvicorn
4. python app.py
5. Open http://localhost:8502
"""

import json
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import asyncio
import uvicorn
import secrets
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

security = HTTPBasic()

DASHBOARD_USER = "bagwork"
DASHBOARD_PASS = "MoneyMonkeys"

def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, DASHBOARD_USER)
    correct_pass = secrets.compare_digest(credentials.password, DASHBOARD_PASS)
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

app = FastAPI(title="Profit Tracker Dashboard", version="1.0.0", dependencies=[Depends(verify_auth)])

# Absolute paths
WORKSPACE_DIR = Path("/Users/saa/.openclaw/workspace")
BASE_DIR = WORKSPACE_DIR / "profit-tracker"
STATE_FILE = BASE_DIR / "state" / "state.json"
MEETINGS_DIR = BASE_DIR / "meetings"
DOCS_DIR = BASE_DIR / "docs"
TASKS_FILE = BASE_DIR / "meetings" / "sprint-01" / "tasks.json"

# Multi-project: scan workspace for projects with state/state.json
PROJECTS_CONFIG = {
    "profit-tracker": {"emoji": "💰", "description": "Real-time profit tracking app for event sellers. Offline-first, sub-10s transaction logging."},
    "indian-fashion-brand": {"emoji": "👔", "description": "Premium Indian formal wear × athleisure comfort brand."},
    "technaysh": {"emoji": "📱", "description": "TikTok carousel content generator for tech niche."},
}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class StateUpdate(BaseModel):
    data: Dict

def safe_read_json(file_path: Path, default=None):
    """Safely read JSON file with error handling"""
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return default or {}

def safe_read_text(file_path: Path, default=""):
    """Safely read text file with error handling"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return default

def get_meeting_type_from_filename(filename: str) -> str:
    """Determine meeting type from filename"""
    name = filename.lower()
    if 'kickoff' in name:
        return '🏁'
    elif 'standup' in name:
        return '🔄'
    elif 'bug' in name or 'triage' in name:
        return '🐛'
    elif 'review' in name:
        return '🔍'
    elif 'release' in name or 'retro' in name:
        return '🚀'
    else:
        return '📝'

def get_meeting_display_name(filename: str, file_path: Path) -> str:
    """Get improved display name for meeting"""
    # Check if file is inside sprint folder
    path_parts = file_path.parts
    sprint_prefix = ""
    if any('sprint' in part.lower() for part in path_parts):
        for part in path_parts:
            if 'sprint' in part.lower():
                sprint_num = ''.join(c for c in part if c.isdigit())
                if sprint_num:
                    sprint_prefix = f"Sprint {sprint_num} — "
                break
    
    # Clean up filename
    name = filename.lower().replace('.md', '')
    
    # Handle specific meeting types
    if 'kickoff' in name:
        return sprint_prefix + "Kickoff"
    elif 'standup' in name:
        return sprint_prefix + "Daily Standup"
    elif 'retro' in name:
        return sprint_prefix + "Sprint Retrospective"
    elif 'review' in name:
        return sprint_prefix + "Code Review"
    elif 'planning' in name:
        return sprint_prefix + "Planning"
    
    # For generic meeting files (meeting-YYYY-MM-DD-HHMMSS), try to read first line
    if name.startswith('meeting-'):
        try:
            first_line = safe_read_text(file_path).split('\n')[0].strip()
            if first_line.startswith('#'):
                # Extract heading text
                display_name = first_line.lstrip('# ').strip()
                if display_name:
                    return display_name
        except Exception:
            pass
        
        # Fallback to formatted timestamp
        try:
            # Extract timestamp from filename: meeting-YYYY-MM-DD-HHMMSS
            timestamp_part = name.replace('meeting-', '')
            if len(timestamp_part) >= 15:  # YYYY-MM-DD-HHMMSS format
                date_part = timestamp_part[:10]  # YYYY-MM-DD
                return f"Meeting — {date_part}"
        except Exception:
            pass
    
    # Default: clean up filename
    return name.replace('-', ' ').replace('_', ' ').title()

@app.get("/")
async def root():
    """Serve the landing page"""
    return FileResponse("static/landing.html")

@app.get("/project/{slug}")
async def project_dashboard(slug: str):
    """Serve the project dashboard"""
    return FileResponse("static/index.html")

@app.get("/api/projects")
async def list_projects():
    """List all projects in workspace that have state files"""
    projects = []
    for dir_path in sorted(WORKSPACE_DIR.iterdir()):
        state_file = dir_path / "state" / "state.json"
        if not state_file.exists():
            continue
        slug = dir_path.name
        state = safe_read_json(state_file, {})
        config = PROJECTS_CONFIG.get(slug, {})
        tasks = state.get("tasks", [])
        done = sum(1 for t in tasks if t.get("status") == "done")
        agents = state.get("agents", {})
        active = sum(1 for a in agents.values() if a.get("status") not in ("idle", None))
        projects.append({
            "slug": slug,
            "name": state.get("project", slug.replace("-", " ").title()),
            "emoji": config.get("emoji", "📦"),
            "description": config.get("description", ""),
            "phase": state.get("phase", "unknown").title(),
            "sprint": state.get("currentSprint", 0),
            "tasks_total": len(tasks),
            "tasks_done": done,
            "agents_active": active,
            "status": state.get("status", "unknown"),
        })
    return JSONResponse({"projects": projects})

def get_project_paths(slug: str = None):
    """Resolve project directory paths from slug"""
    if slug:
        base = WORKSPACE_DIR / slug
    else:
        base = BASE_DIR  # default to profit-tracker
    return {
        "base": base,
        "state": base / "state" / "state.json",
        "meetings": base / "meetings",
        "docs": base / "docs",
        "tasks": base / "meetings" / "sprint-01" / "tasks.json",
    }

AGENT_META = {
    "architect": {"name": "Alex", "emoji": "🏗️", "role": "System Design"},
    "frontend":  {"name": "Frankie", "emoji": "🎨", "role": "UI/UX"},
    "backend":   {"name": "Blake", "emoji": "⚙️", "role": "API & Data"},
    "qa":        {"name": "Quinn", "emoji": "🔍", "role": "Testing"},
    "bugfix":    {"name": "Bug Fixer", "emoji": "🐛", "role": "Debugging"},
}

@app.get("/api/state")
async def get_state(project: str = None):
    """Get current state data — transforms state.json into dashboard format"""
    paths = get_project_paths(project)
    raw = safe_read_json(paths["state"], {})

    # If already in dashboard format (has project.name), return as-is
    if isinstance(raw.get("project"), dict):
        return JSONResponse(raw)

    # Transform state.json → dashboard format
    tasks = raw.get("tasks", [])
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    total_count = len(tasks)
    progress = done_count / total_count if total_count else 0

    # Project info
    project = {
        "name": raw.get("project", "PROFIT TRACKER"),
        "sprint": raw.get("currentSprint", 0),
        "phase": raw.get("phase", "initializing").title(),
        "progress": round(progress, 2),
        "uptime": "Sprint 1",
    }

    # Agents — merge meta with live status
    agents = {}
    for key, agent_data in raw.get("agents", {}).items():
        meta = AGENT_META.get(key, {"name": key.title(), "emoji": "🤖", "role": "Agent"})
        agents[key] = {
            "name": meta["name"],
            "emoji": meta["emoji"],
            "role": meta["role"],
            "status": agent_data.get("status", "idle"),
            "task": agent_data.get("task"),
            "last_action": agent_data.get("lastAction"),
            "startedAt": agent_data.get("startedAt"),
        }

    # Metrics
    m = raw.get("metrics", {})
    metrics = {
        "tasks_completed": m.get("tasksDone", done_count),
        "tasks_total": m.get("tasksTotal", total_count),
        "bugs_found": m.get("bugsFound", 0),
        "bugs_fixed": m.get("bugsFixed", 0),
        "tests_passing": m.get("testsPassing", 0),
        "tests_failing": m.get("testsFailing", 0),
        "lines_of_code": m.get("linesOfCode", 0),
    }

    # Activity log
    activity_log = []
    for entry in raw.get("log", [])[-20:]:
        activity_log.append({
            "timestamp": entry.get("ts", ""),
            "agent": entry.get("agent", "system"),
            "action": entry.get("action", ""),
            "type": "success",
        })

    return JSONResponse({
        "project": project,
        "agents": agents,
        "metrics": metrics,
        "activity_log": activity_log,
    })

@app.post("/api/state")
async def update_state(update: StateUpdate):
    """Update state data (for agents to push updates)"""
    try:
        current_state = safe_read_json(STATE_FILE, {})
        current_state.update(update.data)
        
        # Ensure state directory exists
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(STATE_FILE, 'w') as f:
            json.dump(current_state, f, indent=2)
        
        return {"status": "success", "message": "State updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meetings")
async def get_meetings(project: str = None):
    """List all meeting files"""
    paths = get_project_paths(project)
    meetings_dir = paths["meetings"]
    meetings = []
    try:
        if meetings_dir.exists():
            for file_path in glob.glob(str(meetings_dir / "**" / "*.md"), recursive=True):
                path = Path(file_path)
                rel_path = path.relative_to(meetings_dir)
                meetings.append({
                    "path": str(rel_path),
                    "name": get_meeting_display_name(path.stem, path),
                    "type": get_meeting_type_from_filename(path.name),
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None
                })
    except Exception as e:
        print(f"Error listing meetings: {e}")
    
    return JSONResponse({"meetings": sorted(meetings, key=lambda x: x.get('modified', ''), reverse=True)})

@app.get("/api/meeting-content/{path:path}")
async def get_meeting(path: str, project: str = None):
    """Get meeting content by path"""
    try:
        paths = get_project_paths(project)
        meeting_file = paths["meetings"] / path
        if not meeting_file.exists():
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        content = safe_read_text(meeting_file)
        return JSONResponse({
            "path": path,
            "content": content,
            "type": get_meeting_type_from_filename(path)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs")
async def get_docs(project: str = None):
    """List all documentation files"""
    paths = get_project_paths(project)
    docs_dir = paths["docs"]
    docs = []
    try:
        if docs_dir.exists():
            for file_path in glob.glob(str(docs_dir / "*.md")):
                path = Path(file_path)
                docs.append({
                    "filename": path.name,
                    "name": path.stem.replace('-', ' ').title(),
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None
                })
    except Exception as e:
        print(f"Error listing docs: {e}")
    
    return JSONResponse({"docs": sorted(docs, key=lambda x: x.get('modified', ''), reverse=True)})

@app.get("/api/doc/{filename}")
async def get_doc(filename: str, project: str = None):
    """Get documentation content by filename"""
    try:
        paths = get_project_paths(project)
        doc_file = paths["docs"] / filename
        if not doc_file.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        content = safe_read_text(doc_file)
        return JSONResponse({
            "filename": filename,
            "content": content
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks")
async def get_tasks(project: str = None, sprint: int = None):
    """Get tasks data — reads flat array from tasks.json OR state.json and groups by status"""
    paths = get_project_paths(project)
    # Prefer state.json tasks (agents update this), fall back to tasks.json
    state = safe_read_json(paths["state"], {})
    raw = state.get("tasks", [])
    if not raw:
        raw = safe_read_json(paths["tasks"], [])
    
    # If it's already grouped (object with column keys), return as-is
    if isinstance(raw, dict) and any(k in raw for k in ["backlog", "in_dev", "in_qa", "done"]):
        # For pre-grouped data, we can't easily filter by sprint, so return as-is
        return JSONResponse(raw)
    
    # Filter by sprint if specified
    if isinstance(raw, list):
        if sprint is not None:
            raw = [task for task in raw if task.get("sprint") == sprint]
        elif state.get("currentSprint"):
            # If no sprint specified, show current sprint by default
            current_sprint = state.get("currentSprint")
            raw = [task for task in raw if task.get("sprint") == current_sprint]
    
    # Otherwise group flat array by status
    STATUS_MAP = {"todo": "backlog", "in-progress": "in_dev", "in_dev": "in_dev", "in_qa": "in_qa", "done": "done", "backlog": "backlog"}
    grouped = {"backlog": [], "in_dev": [], "in_qa": [], "done": []}
    if isinstance(raw, list):
        for task in raw:
            status = task.get("status", "backlog")
            column = STATUS_MAP.get(status, "backlog")
            grouped[column].append(task)
    return JSONResponse(grouped)

@app.get("/api/log")
async def get_activity_log(project: str = None):
    """Get activity log"""
    paths = get_project_paths(project)
    state = safe_read_json(paths["state"], {})
    raw_log = state.get("log", state.get("activity_log", []))
    # Transform to dashboard format
    entries = []
    for entry in raw_log[-30:]:
        entries.append({
            "timestamp": entry.get("ts", entry.get("timestamp", "")),
            "agent": entry.get("agent", "system"),
            "action": entry.get("action", ""),
            "type": entry.get("type", "success"),
        })
    return JSONResponse(entries)

# === Sprint Control Endpoints ===

@app.get("/api/sprint/status", dependencies=[Depends(verify_auth)])
async def sprint_status(project: str = None):
    """Get current sprint status and running state"""
    paths = get_project_paths(project)
    state = safe_read_json(paths["state"], {})
    
    # Determine if sprint is "running" based on status and active tasks
    status = state.get("status", "idle")
    is_running = status in ["active", "paused"]
    
    return JSONResponse({
        "running": is_running,  # Keep existing format for backward compatibility
        "error": "",
        "status": status,
        "sprint": state.get("currentSprint", 0),
        "phase": state.get("phase", "initializing")
    })

@app.post("/api/sprint/pause", dependencies=[Depends(verify_auth)])
async def pause_sprint(project: str = None):
    """Pause the current sprint - sets status to paused, all active agents to paused"""
    try:
        paths = get_project_paths(project)
        state = safe_read_json(paths["state"], {})
        
        # Store previous agent statuses before pausing
        agents = state.get("agents", {})
        for agent_key, agent_data in agents.items():
            if agent_data.get("status") in ["active", "working"]:
                agent_data["prev_status"] = agent_data.get("status")
                agent_data["status"] = "paused"
        
        # Set global status to paused
        state["status"] = "paused"
        
        # Add log entry
        if "log" not in state:
            state["log"] = []
        state["log"].append({
            "ts": datetime.now().isoformat(),
            "agent": "system",
            "action": f"Sprint {state.get('currentSprint', '?')} paused by user"
        })
        
        # Save state
        with open(paths["state"], 'w') as f:
            json.dump(state, f, indent=2)
        
        return JSONResponse({"status": "success", "message": "Sprint paused"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sprint/resume", dependencies=[Depends(verify_auth)])
async def resume_sprint(project: str = None):
    """Resume the paused sprint - sets status to active, restore paused agents to previous status"""
    try:
        paths = get_project_paths(project)
        state = safe_read_json(paths["state"], {})
        
        # Restore previous agent statuses
        agents = state.get("agents", {})
        for agent_key, agent_data in agents.items():
            if agent_data.get("status") == "paused":
                prev_status = agent_data.get("prev_status", "idle")
                agent_data["status"] = prev_status
                if "prev_status" in agent_data:
                    del agent_data["prev_status"]
        
        # Set global status to active
        state["status"] = "active"
        
        # Add log entry
        if "log" not in state:
            state["log"] = []
        state["log"].append({
            "ts": datetime.now().isoformat(),
            "agent": "system",
            "action": f"Sprint {state.get('currentSprint', '?')} resumed by user"
        })
        
        # Save state
        with open(paths["state"], 'w') as f:
            json.dump(state, f, indent=2)
        
        return JSONResponse({"status": "success", "message": "Sprint resumed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SprintCompleteBody(BaseModel):
    project: Optional[str] = None

@app.post("/api/sprint/complete", dependencies=[Depends(verify_auth)])
async def complete_sprint(body: SprintCompleteBody):
    """Complete current sprint - set phase/status, agents to idle, log completion"""
    try:
        paths = get_project_paths(body.project)
        state = safe_read_json(paths["state"], {})
        
        current_sprint = state.get("currentSprint", 0)
        tasks = state.get("tasks", [])
        
        # Calculate summary stats
        sprint_tasks = [t for t in tasks if t.get("sprint") == current_sprint]
        tasks_done = len([t for t in sprint_tasks if t.get("status") == "done"])
        bugs_found = len([b for b in state.get("bugs", []) if b.get("sprint") == current_sprint])
        meetings_held = len([m for m in state.get("meetings", []) if str(current_sprint) in m.get("file", "")])
        
        # Set all agents to idle
        agents = state.get("agents", {})
        for agent_key, agent_data in agents.items():
            agent_data["status"] = "idle"
            agent_data["task"] = None
        
        # Update state
        state["phase"] = "complete"
        state["status"] = "idle"
        
        # Add completion log
        if "log" not in state:
            state["log"] = []
        state["log"].append({
            "ts": datetime.now().isoformat(),
            "agent": "system",
            "action": f"Sprint {current_sprint} completed - {tasks_done}/{len(sprint_tasks)} tasks done, {bugs_found} bugs found, {meetings_held} meetings held"
        })
        
        # Save state
        with open(paths["state"], 'w') as f:
            json.dump(state, f, indent=2)
        
        return JSONResponse({
            "status": "success",
            "summary": {
                "sprint": current_sprint,
                "tasks_total": len(sprint_tasks),
                "tasks_done": tasks_done,
                "bugs_found": bugs_found,
                "bugs_fixed": len([b for b in state.get("bugs", []) if b.get("sprint") == current_sprint and b.get("status") == "fixed"]),
                "meetings_held": meetings_held
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class NewSprintTask(BaseModel):
    title: str
    assignee: str
    priority: str
    description: Optional[str] = None

class NewSprintBody(BaseModel):
    sprint_number: int
    goals: List[str]
    tasks: List[NewSprintTask]
    project: Optional[str] = None

@app.post("/api/sprint/new", dependencies=[Depends(verify_auth)])
async def create_new_sprint(body: NewSprintBody):
    """Create a new sprint with goals and tasks"""
    try:
        paths = get_project_paths(body.project)
        state = safe_read_json(paths["state"], {})
        
        # Update sprint number and state
        state["currentSprint"] = body.sprint_number
        state["phase"] = "sprint_planning"
        state["status"] = "active"
        
        # Reset agent statuses
        agents = state.get("agents", {})
        for agent_key, agent_data in agents.items():
            agent_data["status"] = "idle"
            agent_data["task"] = None
        
        # Generate new task IDs
        existing_tasks = state.get("tasks", [])
        max_id = 0
        for task in existing_tasks:
            task_id = task.get("id", "T-000")
            try:
                num = int(task_id.split("-")[1])
                max_id = max(max_id, num)
            except:
                pass
        
        # Add new tasks
        new_tasks = []
        for i, task_data in enumerate(body.tasks):
            task_id = f"T-{max_id + i + 1:03d}"
            new_task = {
                "id": task_id,
                "title": task_data.title,
                "assignee": task_data.assignee,
                "priority": task_data.priority,
                "status": "backlog",
                "sprint": body.sprint_number,
                "agent": task_data.assignee
            }
            if task_data.description:
                new_task["description"] = task_data.description
            new_tasks.append(new_task)
        
        # Add new tasks to state
        if "tasks" not in state:
            state["tasks"] = []
        state["tasks"].extend(new_tasks)
        
        # Add log entry
        if "log" not in state:
            state["log"] = []
        state["log"].append({
            "ts": datetime.now().isoformat(),
            "agent": "system",
            "action": f"Sprint {body.sprint_number} created - {len(new_tasks)} tasks, {len(body.goals)} goals"
        })
        
        # Save state
        with open(paths["state"], 'w') as f:
            json.dump(state, f, indent=2)
        
        return JSONResponse({
            "status": "success",
            "sprint": {
                "number": body.sprint_number,
                "goals": body.goals,
                "tasks_added": len(new_tasks),
                "phase": "sprint_planning"
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sprint/summary", dependencies=[Depends(verify_auth)])
async def get_sprint_summary(project: str = None):
    """Get current sprint summary with task breakdown and agent performance"""
    paths = get_project_paths(project)
    state = safe_read_json(paths["state"], {})
    
    current_sprint = state.get("currentSprint", 0)
    tasks = state.get("tasks", [])
    sprint_tasks = [t for t in tasks if t.get("sprint") == current_sprint]
    
    # Task breakdown by status
    task_breakdown = {
        "backlog": len([t for t in sprint_tasks if t.get("status") == "backlog"]),
        "in_dev": len([t for t in sprint_tasks if t.get("status") in ["in_dev", "in-progress"]]),
        "in_qa": len([t for t in sprint_tasks if t.get("status") == "in_qa"]),
        "done": len([t for t in sprint_tasks if t.get("status") == "done"])
    }
    
    completion_percentage = round((task_breakdown["done"] / len(sprint_tasks)) * 100) if sprint_tasks else 0
    
    # Agent performance
    agent_performance = {}
    for task in [t for t in sprint_tasks if t.get("status") == "done"]:
        agent = task.get("assignee") or task.get("agent", "unknown")
        if agent not in agent_performance:
            agent_performance[agent] = 0
        agent_performance[agent] += 1
    
    # Meetings and bugs for this sprint
    meetings_held = len([m for m in state.get("meetings", []) if str(current_sprint) in m.get("file", "")])
    bugs_found = len([b for b in state.get("bugs", []) if b.get("sprint") == current_sprint])
    bugs_fixed = len([b for b in state.get("bugs", []) if b.get("sprint") == current_sprint and b.get("status") == "fixed"])
    
    return JSONResponse({
        "sprint": current_sprint,
        "completion_percentage": completion_percentage,
        "tasks": task_breakdown,
        "agent_performance": agent_performance,
        "meetings_held": meetings_held,
        "bugs_found": bugs_found,
        "bugs_fixed": bugs_fixed,
        "phase": state.get("phase", "unknown"),
        "status": state.get("status", "unknown")
    })

# === Meeting Spy Endpoints ===

class MeetingWriteBody(BaseModel):
    project: str
    agent: str
    text: str
    meeting_type: Optional[str] = None

class MeetingEndBody(BaseModel):
    project: str
    meeting_type: Optional[str] = None

@app.get("/api/meeting/latest")
async def meeting_latest(project: str = None):
    """Return the latest meeting transcript as JSONL-style messages for the spy view"""
    paths = get_project_paths(project)
    meetings_dir = paths["meetings"]
    if not meetings_dir.exists():
        return JSONResponse({"messages": [], "name": None})
    # Find most recent .md meeting file
    md_files = sorted(glob.glob(str(meetings_dir / "**" / "*.md"), recursive=True),
                      key=lambda f: Path(f).stat().st_mtime, reverse=True)
    if not md_files:
        return JSONResponse({"messages": [], "name": None})
    latest = Path(md_files[0])
    content = safe_read_text(latest)
    name = get_meeting_display_name(latest.stem, latest)
    # Parse markdown transcript into messages
    messages = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("**[") and "]" in line and ":**" in line:
            try:
                ts_part = line.split("]")[0].replace("**[", "")
                rest = line.split(":**", 1)
                speaker_part = rest[0].split("] ")[-1].replace("**", "").strip()
                text = rest[1].strip() if len(rest) > 1 else ""
                emoji = speaker_part.split(" ")[0] if speaker_part else "🤖"
                speaker = " ".join(speaker_part.split(" ")[1:]) if " " in speaker_part else speaker_part
                # Map speaker back to agent key
                agent_key = "system"
                for k, v in AGENT_META.items():
                    if v["name"] == speaker:
                        agent_key = k
                        break
                messages.append({"ts": ts_part, "agent": agent_key, "speaker": speaker, "emoji": emoji, "text": text})
            except Exception:
                pass
    return JSONResponse({"messages": messages, "name": name, "path": str(latest.relative_to(meetings_dir)),
                         "modified": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()})

@app.get("/api/meeting/active")
async def meeting_active(project: str = None):
    paths = get_project_paths(project)
    live_file = paths["meetings"] / "live-meeting.jsonl"
    if not live_file.exists():
        return JSONResponse({"active": False, "file": None, "lines": 0, "started": None})
    lines = live_file.read_text().strip().split("\n")
    lines = [l for l in lines if l.strip()]
    started = None
    if lines:
        try:
            started = json.loads(lines[0]).get("ts")
        except Exception:
            pass
    return JSONResponse({"active": True, "file": str(live_file), "lines": len(lines), "started": started})

@app.get("/api/meeting/stream")
async def meeting_stream(project: str = None):
    paths = get_project_paths(project)
    live_file = paths["meetings"] / "live-meeting.jsonl"

    async def event_generator():
        # Bail immediately if no active meeting
        if not live_file.exists():
            yield "data: {\"event\":\"no_meeting\"}\n\n"
            return
        last_line = 0
        last_change = datetime.now()
        keepalive_counter = 0
        while True:
            if live_file.exists():
                lines = live_file.read_text().strip().split("\n")
                lines = [l for l in lines if l.strip()]
                if len(lines) > last_line:
                    for line in lines[last_line:]:
                        yield f"data: {line}\n\n"
                    last_line = len(lines)
                    last_change = datetime.now()
            else:
                if last_line > 0:
                    yield "data: {\"event\":\"done\"}\n\n"
                    return
            if (datetime.now() - last_change).total_seconds() > 30:
                yield "data: {\"event\":\"done\"}\n\n"
                return
            keepalive_counter += 1
            if keepalive_counter >= 10:
                yield ": keepalive\n\n"
                keepalive_counter = 0
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/api/meeting/write")
async def meeting_write(body: MeetingWriteBody):
    paths = get_project_paths(body.project)
    meetings_dir = paths["meetings"]
    meetings_dir.mkdir(parents=True, exist_ok=True)
    live_file = meetings_dir / "live-meeting.jsonl"
    meta = AGENT_META.get(body.agent, {"name": body.agent.title(), "emoji": "🤖"})
    line = json.dumps({
        "ts": datetime.now().isoformat(),
        "agent": body.agent,
        "speaker": meta["name"],
        "emoji": meta.get("emoji", "🤖"),
        "text": body.text,
        "meeting_type": body.meeting_type,
    })
    with open(live_file, "a") as f:
        f.write(line + "\n")
    return {"status": "ok"}

@app.post("/api/meeting/end")
async def meeting_end(body: MeetingEndBody):
    paths = get_project_paths(body.project)
    live_file = paths["meetings"] / "live-meeting.jsonl"
    if not live_file.exists():
        raise HTTPException(status_code=404, detail="No active meeting")
    lines = [l for l in live_file.read_text().strip().split("\n") if l.strip()]
    entries = [json.loads(l) for l in lines]
    
    # Determine meeting type from body or first entry
    meeting_type = body.meeting_type
    if not meeting_type and entries:
        meeting_type = entries[0].get("meeting_type")
    
    # Build filename based on meeting type
    ts_str = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    if meeting_type:
        # Map meeting types to filenames
        type_map = {
            "kickoff": "kickoff",
            "standup": "standup", 
            "retro": "retro",
            "retrospective": "retro",
            "review": "review",
            "planning": "planning",
            "ad-hoc": "adhoc"
        }
        type_filename = type_map.get(meeting_type.lower(), meeting_type.lower())
        
        # Try to determine current sprint for sprint folder
        state = safe_read_json(paths["base"] / "state" / "state.json", {})
        current_sprint = state.get("currentSprint")
        if current_sprint:
            sprint_folder = paths["meetings"] / f"sprint-{current_sprint:02d}"
            sprint_folder.mkdir(exist_ok=True)
            out_file = sprint_folder / f"{type_filename}.md"
        else:
            out_file = paths["meetings"] / f"{type_filename}-{ts_str}.md"
    else:
        out_file = paths["meetings"] / f"meeting-{ts_str}.md"
    
    # Build markdown transcript
    md_lines = [f"# {meeting_type.title() if meeting_type else 'Meeting'} Transcript — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    participants = set()
    for e in entries:
        participants.add(f"{e.get('emoji','')} {e.get('speaker','')}")
        t = e.get("ts", "")
        try:
            t = datetime.fromisoformat(t).strftime("%H:%M:%S")
        except Exception:
            pass
        md_lines.append(f"**[{t}] {e.get('emoji','')} {e.get('speaker','')}:** {e.get('text','')}\n")
    md_lines.insert(1, f"\n**Participants:** {', '.join(sorted(participants))}\n")
    md_lines.insert(2, f"**Messages:** {len(entries)}\n\n---\n")
    
    out_file.write_text("\n".join(md_lines))
    live_file.unlink()
    return {"status": "ok", "path": str(out_file), "messages": len(entries), "participants": list(participants)}

if __name__ == "__main__":
    print("🚀 Starting Profit Tracker Dashboard on http://localhost:8502")
    uvicorn.run(app, host="0.0.0.0", port=8502, log_level="info")