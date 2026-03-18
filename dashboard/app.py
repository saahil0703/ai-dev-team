#!/usr/bin/env python3
"""
AI Dev Team Platform — Dashboard Server
FastAPI app with auth, real-time dashboard, meeting spy, and sprint triggers.
"""
import json
import os
import sys
import glob
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="AI Dev Team Platform", version="2.0.0")

# Paths
BASE_DIR = Path(__file__).parent.parent
STATE_FILE = BASE_DIR / "state" / "state.json"
MEETINGS_DIR = BASE_DIR / "meetings"
DOCS_DIR = BASE_DIR / "docs"

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─── Auth ───────────────────────────────────────────────────────────────────
from dashboard.auth import auth_manager, auth_middleware

app.middleware("http")(auth_middleware)

class LoginRequest(BaseModel):
    invite_code: str

@app.get("/login")
async def login_page():
    return FileResponse(str(STATIC_DIR / "login.html"))

@app.post("/auth/login")
async def auth_login(req: LoginRequest, response: Response):
    try:
        token = auth_manager.create_session(req.invite_code)
        response = JSONResponse({"status": "ok"})
        response.set_cookie("ai_dev_session", token, httponly=True, max_age=86400, samesite="lax")
        return response
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid invite code")

@app.post("/auth/logout")
async def auth_logout(response: Response, session: Optional[str] = Cookie(None, alias="ai_dev_session")):
    if session:
        auth_manager.delete_session(session)
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie("ai_dev_session")
    return resp

# ─── Agent Meta ─────────────────────────────────────────────────────────────
AGENT_META = {
    "architect": {"name": "Alex", "emoji": "🏗️", "role": "System Design"},
    "frontend":  {"name": "Frankie", "emoji": "🎨", "role": "UI/UX"},
    "backend":   {"name": "Blake", "emoji": "⚙️", "role": "API & Data"},
    "qa":        {"name": "Quinn", "emoji": "🔍", "role": "Testing"},
    "bugfix":    {"name": "Bug Fixer", "emoji": "🐛", "role": "Debugging"},
}

# ─── Helpers ────────────────────────────────────────────────────────────────
def safe_read_json(file_path: Path, default=None):
    try:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return default or {}

def safe_read_text(file_path: Path, default=""):
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return default

# ─── Pages ──────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "landing.html"))

@app.get("/project/{slug}")
async def project_dashboard(slug: str):
    return FileResponse(str(STATIC_DIR / "index.html"))

# ─── API: Projects ──────────────────────────────────────────────────────────
@app.get("/api/projects")
async def list_projects():
    state = safe_read_json(STATE_FILE, {})
    tasks = state.get("tasks", [])
    done = sum(1 for t in tasks if t.get("status") == "done")
    agents = state.get("agents", {})
    active = sum(1 for a in agents.values() if a.get("status") not in ("idle", None))
    projects = [{
        "slug": "ai-dev-team",
        "name": state.get("project", "AI Dev Team"),
        "emoji": "🤖",
        "description": "AI-powered development team",
        "phase": state.get("phase", "idle").title(),
        "sprint": state.get("currentSprint", 0),
        "tasks_total": len(tasks),
        "tasks_done": done,
        "agents_active": active,
        "status": state.get("status", "idle"),
    }]
    return JSONResponse({"projects": projects})

# ─── API: State ─────────────────────────────────────────────────────────────
@app.get("/api/state")
async def get_state(project: str = None):
    raw = safe_read_json(STATE_FILE, {})
    if isinstance(raw.get("project"), dict):
        return JSONResponse(raw)

    tasks = raw.get("tasks", [])
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    total_count = len(tasks)
    progress = done_count / total_count if total_count else 0

    project_info = {
        "name": raw.get("project", "AI Dev Team"),
        "sprint": raw.get("currentSprint", 0),
        "phase": raw.get("phase", "idle").title(),
        "progress": round(progress, 2),
        "uptime": f"Sprint {raw.get('currentSprint', 0)}",
    }

    agents = {}
    for key, agent_data in raw.get("agents", {}).items():
        meta = AGENT_META.get(key, {"name": key.title(), "emoji": "🤖", "role": "Agent"})
        agents[key] = {
            "name": meta["name"], "emoji": meta["emoji"], "role": meta["role"],
            "status": agent_data.get("status", "idle"),
            "task": agent_data.get("task"),
            "last_action": agent_data.get("lastAction"),
            "startedAt": agent_data.get("startedAt"),
        }

    m = raw.get("metrics", {})
    metrics = {
        "tasks_completed": m.get("tasksDone", done_count),
        "tasks_total": m.get("tasksTotal", total_count),
        "bugs_found": m.get("bugsFound", 0), "bugs_fixed": m.get("bugsFixed", 0),
        "tests_passing": m.get("testsPassing", 0), "tests_failing": m.get("testsFailing", 0),
        "lines_of_code": m.get("linesOfCode", 0),
    }

    activity_log = []
    for entry in raw.get("log", [])[-20:]:
        activity_log.append({
            "timestamp": entry.get("ts", ""), "agent": entry.get("agent", "system"),
            "action": entry.get("action", ""), "type": "success",
        })

    return JSONResponse({"project": project_info, "agents": agents, "metrics": metrics, "activity_log": activity_log})

class StateUpdate(BaseModel):
    data: Dict

@app.post("/api/state")
async def update_state(update: StateUpdate):
    current = safe_read_json(STATE_FILE, {})
    current.update(update.data)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(current, f, indent=2)
    return {"status": "success"}

# ─── API: Tasks ─────────────────────────────────────────────────────────────
@app.get("/api/tasks")
async def get_tasks(project: str = None):
    state = safe_read_json(STATE_FILE, {})
    raw = state.get("tasks", [])
    STATUS_MAP = {"todo": "backlog", "in-progress": "in_dev", "in_dev": "in_dev", "in_qa": "in_qa", "done": "done", "backlog": "backlog"}
    grouped = {"backlog": [], "in_dev": [], "in_qa": [], "done": []}
    if isinstance(raw, list):
        for task in raw:
            column = STATUS_MAP.get(task.get("status", "backlog"), "backlog")
            grouped[column].append(task)
    return JSONResponse(grouped)

# ─── API: Activity Log ─────────────────────────────────────────────────────
@app.get("/api/log")
async def get_activity_log(project: str = None):
    state = safe_read_json(STATE_FILE, {})
    raw_log = state.get("log", [])
    entries = []
    for entry in raw_log[-30:]:
        entries.append({
            "timestamp": entry.get("ts", ""), "agent": entry.get("agent", "system"),
            "action": entry.get("action", ""), "type": entry.get("type", "success"),
        })
    return JSONResponse(entries)

# ─── API: Meetings ──────────────────────────────────────────────────────────
@app.get("/api/meetings")
async def get_meetings(project: str = None):
    meetings = []
    if MEETINGS_DIR.exists():
        for fp in glob.glob(str(MEETINGS_DIR / "**" / "*.md"), recursive=True):
            p = Path(fp)
            rel = p.relative_to(MEETINGS_DIR)
            name = p.stem.replace('-', ' ').title()
            mtype = '🏁 Kickoff' if 'kickoff' in p.name.lower() else '🔄 Standup' if 'standup' in p.name.lower() else '📝 Meeting'
            meetings.append({"path": str(rel), "name": name, "type": mtype,
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
    return JSONResponse({"meetings": sorted(meetings, key=lambda x: x.get('modified', ''), reverse=True)})

@app.get("/api/meeting/{path:path}")
async def get_meeting(path: str, project: str = None):
    fp = MEETINGS_DIR / path
    if not fp.exists():
        raise HTTPException(404, "Meeting not found")
    return JSONResponse({"path": path, "content": safe_read_text(fp)})

# ─── API: Docs ──────────────────────────────────────────────────────────────
@app.get("/api/docs")
async def get_docs(project: str = None):
    docs = []
    if DOCS_DIR.exists():
        for fp in glob.glob(str(DOCS_DIR / "*.md")):
            p = Path(fp)
            docs.append({"filename": p.name, "name": p.stem.replace('-', ' ').title(),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()})
    return JSONResponse({"docs": sorted(docs, key=lambda x: x.get('modified', ''), reverse=True)})

@app.get("/api/doc/{filename}")
async def get_doc(filename: str, project: str = None):
    fp = DOCS_DIR / filename
    if not fp.exists():
        raise HTTPException(404, "Document not found")
    return JSONResponse({"filename": filename, "content": safe_read_text(fp)})

# ─── API: Meeting Spy (Live) ───────────────────────────────────────────────
LIVE_MEETING_FILE = MEETINGS_DIR / "live-meeting.jsonl"

@app.get("/api/meeting/active")
async def meeting_active(project: str = None):
    if LIVE_MEETING_FILE.exists() and LIVE_MEETING_FILE.stat().st_size > 0:
        lines = LIVE_MEETING_FILE.read_text().strip().split('\n')
        first = json.loads(lines[0])
        return JSONResponse({"active": True, "lines": len(lines), "started": first.get("ts")})
    return JSONResponse({"active": False})

@app.get("/api/meeting/stream")
async def meeting_stream(project: str = None):
    async def event_generator():
        last_line = 0
        idle_count = 0
        while True:
            if LIVE_MEETING_FILE.exists():
                lines = LIVE_MEETING_FILE.read_text().strip().split('\n')
                if len(lines) > last_line:
                    for line in lines[last_line:]:
                        if line.strip():
                            yield f"data: {line}\n\n"
                    last_line = len(lines)
                    idle_count = 0
                else:
                    idle_count += 1
            else:
                idle_count += 1

            if idle_count > 120:  # 60s at 500ms
                yield f"event: done\ndata: meeting_ended\n\n"
                break
            if idle_count % 10 == 0:
                yield f": keepalive\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

class MeetingWriteRequest(BaseModel):
    project: Optional[str] = None
    agent: str
    text: str

@app.post("/api/meeting/write")
async def meeting_write(req: MeetingWriteRequest):
    meta = AGENT_META.get(req.agent, {"name": req.agent.title(), "emoji": "🤖"})
    entry = {"ts": datetime.now().isoformat(), "agent": req.agent, "speaker": meta["name"], "emoji": meta["emoji"], "text": req.text}
    MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LIVE_MEETING_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"status": "ok"}

class MeetingEndRequest(BaseModel):
    project: Optional[str] = None

@app.post("/api/meeting/end")
async def meeting_end(req: MeetingEndRequest):
    if not LIVE_MEETING_FILE.exists():
        return {"status": "no_meeting"}
    lines = [json.loads(l) for l in LIVE_MEETING_FILE.read_text().strip().split('\n') if l.strip()]
    participants = list(set(f"{l['emoji']} {l['speaker']}" for l in lines if l.get('agent') != 'system'))
    # Save as markdown
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = MEETINGS_DIR / f"meeting-{ts}.md"
    md = f"# Meeting Transcript — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
    for l in lines:
        md += f"**{l.get('emoji','')} {l.get('speaker','')}:** {l.get('text','')}\n\n"
    md_path.write_text(md)
    LIVE_MEETING_FILE.unlink()
    return {"status": "ok", "path": str(md_path), "messages": len(lines), "participants": participants}

# ─── API: Sprint Trigger ───────────────────────────────────────────────────
sprint_runner = {"running": False, "error": None}

class SprintRequest(BaseModel):
    sprint_number: int
    goals: List[str]

@app.post("/api/sprint/start")
async def start_sprint(req: SprintRequest):
    if sprint_runner["running"]:
        raise HTTPException(409, "A sprint is already running")
    sprint_runner["running"] = True
    sprint_runner["error"] = None

    def run_in_thread():
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            from agents.orchestrator import Orchestrator
            orch = Orchestrator(BASE_DIR)
            loop.run_until_complete(orch.run_sprint(req.sprint_number, req.goals))
        except Exception as e:
            sprint_runner["error"] = str(e)
            print(f"Sprint error: {e}")
        finally:
            sprint_runner["running"] = False
            loop.close()

    threading.Thread(target=run_in_thread, daemon=True).start()
    return {"status": "started", "sprint": req.sprint_number}

@app.get("/api/sprint/status")
async def sprint_status():
    return JSONResponse({"running": sprint_runner["running"], "error": sprint_runner["error"]})

class MeetingStartRequest(BaseModel):
    topic: str
    participants: Optional[List[str]] = None

@app.post("/api/meeting/start")
async def start_meeting(req: MeetingStartRequest):
    if sprint_runner["running"]:
        raise HTTPException(409, "A sprint is already running — meeting in progress")

    def run_in_thread():
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            from agents.orchestrator import Orchestrator
            orch = Orchestrator(BASE_DIR)
            participants = req.participants or ["architect", "frontend", "backend", "qa"]
            loop.run_until_complete(orch.run_ad_hoc_meeting(req.topic, participants))
        except Exception as e:
            print(f"Meeting error: {e}")
        finally:
            loop.close()

    threading.Thread(target=run_in_thread, daemon=True).start()
    return {"status": "started", "topic": req.topic}

# ─── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 AI Dev Team Platform starting on http://localhost:8502")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8502)), log_level="info")
