"""
Orchestrator - Sprint Manager that coordinates all agents
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .architect import ArchitectAgent
from .frontend import FrontendAgent
from .backend import BackendAgent
from .qa import QAAgent
from .meeting import MeetingRunner

class Orchestrator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.state_file = project_dir / "state" / "state.json"
        self.docs_dir = project_dir / "docs"
        
        # Initialize agents
        self.agents = {
            "architect": ArchitectAgent(),
            "frontend": FrontendAgent(),
            "backend": BackendAgent(),
            "qa": QAAgent()
        }
        
        # Initialize meeting runner
        self.meeting_runner = MeetingRunner(project_dir, self.agents)
        
        # Current state
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load current project state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        else:
            return self._create_initial_state()
    
    def _save_state(self):
        """Save current state to file"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _create_initial_state(self) -> Dict:
        """Create initial project state"""
        return {
            "project": "AI Dev Team Platform",
            "status": "initializing",
            "currentSprint": 0,
            "phase": "planning",
            "agents": {
                "architect": {"status": "idle", "task": None, "lastAction": None},
                "frontend": {"status": "idle", "task": None, "lastAction": None},
                "backend": {"status": "idle", "task": None, "lastAction": None},
                "qa": {"status": "idle", "task": None, "lastAction": None}
            },
            "tasks": [],
            "bugs": [],
            "meetings": [],
            "log": [],
            "metrics": {
                "tasksTotal": 0,
                "tasksDone": 0,
                "bugsFound": 0,
                "bugsFixed": 0,
                "testsPassing": 0,
                "testsFailing": 0,
                "linesOfCode": 0
            }
        }
    
    async def run_sprint(self, sprint_number: int, goals: List[str]) -> Dict:
        """
        Run a complete sprint with the AI team
        """
        try:
            self._log_activity("orchestrator", f"Starting Sprint {sprint_number}")
            
            # Update state
            self.state["currentSprint"] = sprint_number
            self.state["phase"] = "sprint_planning"
            self.state["status"] = "active"
            self._save_state()
            
            # 1. Architect designs system
            self._log_activity("orchestrator", "Phase 1: System Design")
            system_design = await self._architect_design_phase(goals)
            
            # 2. Sprint kickoff meeting
            self._log_activity("orchestrator", "Phase 2: Sprint Kickoff Meeting")
            kickoff_result = await self._run_kickoff_meeting(sprint_number, goals, system_design)
            
            # 3. Break down tasks
            self._log_activity("orchestrator", "Phase 3: Task Breakdown")
            tasks = await self._break_down_tasks(goals, system_design)
            
            # 4. Execute sprint
            self._log_activity("orchestrator", "Phase 4: Sprint Execution")
            execution_result = await self._execute_sprint_tasks(tasks)
            
            # 5. QA Review
            self._log_activity("orchestrator", "Phase 5: QA Review")
            qa_result = await self._qa_review_phase(execution_result["completed_tasks"])
            
            # 6. Sprint retrospective
            self._log_activity("orchestrator", "Phase 6: Sprint Retrospective")
            retrospective = await self._run_retrospective(sprint_number, execution_result, qa_result)
            
            # Update final state
            self.state["phase"] = "complete"
            self.state["status"] = "idle"
            self._update_metrics()
            self._save_state()
            
            self._log_activity("orchestrator", f"Sprint {sprint_number} completed successfully")
            
            return {
                "sprint_number": sprint_number,
                "status": "completed",
                "system_design": system_design,
                "tasks_completed": len(execution_result["completed_tasks"]),
                "bugs_found": len(qa_result.get("bugs_found", [])),
                "meetings_held": [kickoff_result["meeting_id"], retrospective["meeting_id"]],
                "duration": "sprint_duration_calculated_here"
            }
            
        except Exception as e:
            self._log_activity("orchestrator", f"Sprint {sprint_number} failed: {str(e)}")
            self.state["phase"] = "error"
            self.state["status"] = f"error: {str(e)}"
            self._save_state()
            raise
    
    async def _architect_design_phase(self, goals: List[str]) -> Dict:
        """Let architect design the system"""
        self._set_agent_status("architect", "active", "Designing system architecture")
        
        architect = self.agents["architect"]
        requirements = {"goals": goals, "constraints": [], "tech_preferences": []}
        
        system_design = await architect.design_system(requirements)
        
        # Save design docs
        self._save_design_docs(system_design)
        
        self._set_agent_status("architect", "idle", "System design completed")
        return system_design
    
    async def _run_kickoff_meeting(self, sprint_number: int, goals: List[str], system_design: Dict) -> Dict:
        """Run sprint kickoff meeting with all agents"""
        topic = f"Sprint {sprint_number} Kickoff"
        agenda = [
            "Review sprint goals and requirements",
            "Present system architecture and technical approach", 
            "Discuss implementation strategy and task assignments",
            "Identify risks and dependencies",
            "Confirm timeline and deliverables"
        ]
        participants = ["architect", "frontend", "backend", "qa"]
        
        context = f"Sprint Goals: {goals}\nSystem Design: {json.dumps(system_design, indent=2)}"
        
        result = await self.meeting_runner.run_meeting(topic, agenda, participants)
        
        # Log meeting in state
        self.state["meetings"].append({
            "name": topic,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "file": result["transcript_file"],
            "participants": participants
        })
        self._save_state()
        
        return result
    
    async def _break_down_tasks(self, goals: List[str], system_design: Dict) -> List[Dict]:
        """Break down sprint goals into specific tasks"""
        self._set_agent_status("architect", "active", "Breaking down sprint into tasks")
        
        architect = self.agents["architect"]
        project_context = {"system_design": system_design, "current_state": self.state}
        
        tasks = await architect.break_down_sprint(project_context, goals)
        
        # Add tasks to state with additional metadata
        task_id_counter = len(self.state["tasks"]) + 1
        for task in tasks:
            if "id" not in task:
                task["id"] = f"T-{task_id_counter:03d}"
                task_id_counter += 1
            
            task["status"] = "backlog"
            task["startedAt"] = None
            task["completedAt"] = None
            task["duration"] = None
            
            self.state["tasks"].append(task)
        
        self._set_agent_status("architect", "idle", f"Created {len(tasks)} tasks")
        self._save_state()
        
        return tasks
    
    async def _execute_sprint_tasks(self, tasks: List[Dict]) -> Dict:
        """Execute sprint tasks with agents working in parallel"""
        completed_tasks = []
        failed_tasks = []
        
        # Group tasks by assignee
        backend_tasks = [t for t in tasks if t.get("assignee") == "backend"]
        frontend_tasks = [t for t in tasks if t.get("assignee") == "frontend"]
        qa_tasks = [t for t in tasks if t.get("assignee") == "qa"]
        
        # Execute backend and frontend tasks in parallel
        async def execute_agent_tasks(agent_key: str, agent_tasks: List[Dict]):
            agent = self.agents[agent_key]
            agent_completed = []
            
            for task in agent_tasks:
                try:
                    self._set_agent_status(agent_key, "working", f"Working on {task['title']}")
                    self._update_task_status(task["id"], "in_dev")
                    
                    # Agent implements the task
                    project_context = {"system_design": {}, "current_tasks": self.state["tasks"]}
                    result = await agent.code(task["title"], project_context)
                    
                    # Mark task as completed
                    task["completedAt"] = datetime.now().isoformat()
                    task["duration"] = "2m 30s"  # Simulated duration
                    task["filesCreated"] = len(result.get("files", []))
                    
                    self._update_task_status(task["id"], "done")
                    agent_completed.append(task)
                    
                    self._log_activity(agent_key, f"Completed task {task['id']}: {task['title']}")
                    
                    # Brief pause between tasks
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self._log_activity(agent_key, f"Failed task {task['id']}: {str(e)}")
                    failed_tasks.append({"task": task, "error": str(e)})
            
            self._set_agent_status(agent_key, "idle", f"Completed {len(agent_completed)} tasks")
            return agent_completed
        
        # Run backend and frontend in parallel
        backend_results, frontend_results = await asyncio.gather(
            execute_agent_tasks("backend", backend_tasks),
            execute_agent_tasks("frontend", frontend_tasks),
            return_exceptions=True
        )
        
        # Handle results
        if isinstance(backend_results, list):
            completed_tasks.extend(backend_results)
        if isinstance(frontend_results, list):
            completed_tasks.extend(frontend_results)
        
        # Execute QA tasks after dev tasks
        if qa_tasks:
            qa_results = await execute_agent_tasks("qa", qa_tasks)
            if isinstance(qa_results, list):
                completed_tasks.extend(qa_results)
        
        return {
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "total_tasks": len(tasks)
        }
    
    async def _qa_review_phase(self, completed_tasks: List[Dict]) -> Dict:
        """QA reviews all completed work"""
        self._set_agent_status("qa", "active", "Reviewing sprint deliverables")
        
        qa = self.agents["qa"]
        bugs_found = []
        
        # Review each completed task
        for task in completed_tasks:
            try:
                test_plan = await qa.create_test_plan(task)
                test_results = await qa.test_feature(task, test_plan)
                
                if test_results.get("bugs_found"):
                    bugs_found.extend(test_results["bugs_found"])
                    
            except Exception as e:
                self._log_activity("qa", f"Error reviewing task {task.get('id', 'unknown')}: {str(e)}")
        
        # Overall release review
        release_decision = await qa.review_release(completed_tasks)
        
        # Update bugs in state
        for bug in bugs_found:
            bug["id"] = f"BUG-{len(self.state['bugs']) + 1:03d}"
            bug["status"] = "open"
            bug["foundAt"] = datetime.now().isoformat()
            self.state["bugs"].append(bug)
        
        self._set_agent_status("qa", "idle", f"Review complete - found {len(bugs_found)} bugs")
        self._save_state()
        
        return {
            "bugs_found": bugs_found,
            "release_decision": release_decision,
            "tasks_reviewed": len(completed_tasks)
        }
    
    async def _run_retrospective(self, sprint_number: int, execution_result: Dict, qa_result: Dict) -> Dict:
        """Run sprint retrospective meeting"""
        topic = f"Sprint {sprint_number} Retrospective"
        agenda = [
            "Review sprint goals vs. actual deliverables",
            "Discuss what went well and what didn't",
            "Analyze bugs found and how to prevent them",
            "Identify process improvements for next sprint",
            "Plan follow-up actions"
        ]
        participants = ["architect", "frontend", "backend", "qa"]
        
        result = await self.meeting_runner.run_meeting(topic, agenda, participants)
        
        # Log meeting in state
        self.state["meetings"].append({
            "name": topic,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "file": result["transcript_file"],
            "participants": participants
        })
        self._save_state()
        
        return result
    
    def _set_agent_status(self, agent_key: str, status: str, task: Optional[str] = None):
        """Update agent status in state"""
        if agent_key not in self.state["agents"]:
            self.state["agents"][agent_key] = {}
            
        self.state["agents"][agent_key]["status"] = status
        self.state["agents"][agent_key]["task"] = task
        self.state["agents"][agent_key]["lastAction"] = task
        
        if status == "working":
            self.state["agents"][agent_key]["startedAt"] = datetime.now().isoformat()
            
        self._save_state()
    
    def _update_task_status(self, task_id: str, status: str):
        """Update task status"""
        for task in self.state["tasks"]:
            if task["id"] == task_id:
                task["status"] = status
                if status == "in_dev":
                    task["startedAt"] = datetime.now().isoformat()
                elif status == "done":
                    task["completedAt"] = datetime.now().isoformat()
                break
        self._save_state()
    
    def _log_activity(self, agent: str, action: str):
        """Log activity to state"""
        self.state["log"].append({
            "ts": datetime.now().isoformat(),
            "agent": agent,
            "action": action
        })
        self._save_state()
    
    def _update_metrics(self):
        """Update project metrics"""
        tasks = self.state["tasks"]
        bugs = self.state["bugs"]
        
        self.state["metrics"] = {
            "tasksTotal": len(tasks),
            "tasksDone": len([t for t in tasks if t.get("status") == "done"]),
            "bugsFound": len(bugs),
            "bugsFixed": len([b for b in bugs if b.get("status") == "fixed"]),
            "testsPassing": 0,  # Would be updated by actual test runs
            "testsFailing": len([b for b in bugs if b.get("status") == "open"]),
            "linesOfCode": sum(t.get("filesCreated", 0) * 50 for t in tasks if t.get("status") == "done")  # Estimate
        }
    
    def _save_design_docs(self, system_design: Dict):
        """Save system design documents"""
        self.docs_dir.mkdir(exist_ok=True)
        
        # Save as JSON and markdown
        with open(self.docs_dir / "system-design.json", "w") as f:
            json.dump(system_design, f, indent=2)
        
        # Create markdown version
        markdown_content = "# System Design\n\n"
        markdown_content += json.dumps(system_design, indent=2)
        
        with open(self.docs_dir / "system-design.md", "w") as f:
            f.write(markdown_content)
    
    async def run_ad_hoc_meeting(self, topic: str, participants: List[str], agenda: Optional[List[str]] = None) -> Dict:
        """Run an ad-hoc meeting on a specific topic"""
        if not agenda:
            agenda = [f"Discuss {topic}"]
            
        result = await self.meeting_runner.run_meeting(topic, agenda, participants)
        
        # Log meeting in state
        self.state["meetings"].append({
            "name": topic,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "file": result["transcript_file"],
            "participants": participants
        })
        self._save_state()
        
        return result
    
    def get_status(self) -> Dict:
        """Get current orchestrator status"""
        return {
            "current_sprint": self.state.get("currentSprint", 0),
            "phase": self.state.get("phase", "idle"),
            "status": self.state.get("status", "idle"),
            "active_agents": len([a for a in self.state.get("agents", {}).values() if a.get("status") != "idle"]),
            "total_tasks": len(self.state.get("tasks", [])),
            "completed_tasks": len([t for t in self.state.get("tasks", []) if t.get("status") == "done"])
        }