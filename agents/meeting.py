"""
Meeting Runner - Facilitates AI agent meetings and discussions
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseAgent

class MeetingRunner:
    def __init__(self, project_dir: Path, agents: Dict[str, BaseAgent]):
        self.project_dir = project_dir
        self.agents = agents
        self.meetings_dir = project_dir / "meetings"
        self.meetings_dir.mkdir(exist_ok=True)
        self.live_meeting_file = self.meetings_dir / "live-meeting.jsonl"
        
    async def run_meeting(self, topic: str, agenda_items: List[str], participants: List[str]) -> Dict:
        """
        Run a meeting with specified agents
        Writes real-time to live-meeting.jsonl for dashboard spy functionality
        """
        # Initialize meeting
        meeting_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        meeting_start = datetime.now()
        
        # Clear any existing live meeting file
        if self.live_meeting_file.exists():
            self.live_meeting_file.unlink()
        
        # Start meeting log
        await self._log_meeting_message("system", "📅 Meeting Facilitator", f"Meeting started: {topic}")
        await self._log_meeting_message("system", "📅 Meeting Facilitator", f"Participants: {', '.join(participants)}")
        
        transcript = []
        
        try:
            # Opening statement
            intro = f"Meeting: {topic}\nAgenda: {', '.join(agenda_items)}\nParticipants: {', '.join(participants)}"
            await self._log_meeting_message("system", "📅 Meeting Facilitator", intro)
            
            # Process each agenda item
            for agenda_item in agenda_items:
                await self._log_meeting_message("system", "📅 Meeting Facilitator", f"📋 Agenda Item: {agenda_item}")
                
                # Round-robin discussion for this agenda item
                item_discussion = await self._run_agenda_item_discussion(agenda_item, participants, topic)
                transcript.extend(item_discussion)
                
                # Brief pause between agenda items
                await asyncio.sleep(1)
            
            # Wrap up meeting
            await self._log_meeting_message("system", "📅 Meeting Facilitator", "✅ Meeting concluded")
            
        except Exception as e:
            await self._log_meeting_message("system", "📅 Meeting Facilitator", f"❌ Meeting error: {str(e)}")
        
        # Calculate meeting duration
        duration = datetime.now() - meeting_start
        
        # Save final transcript
        final_transcript = await self._save_final_transcript(meeting_id, topic, participants, transcript, duration)
        
        return {
            "meeting_id": meeting_id,
            "topic": topic,
            "participants": participants,
            "duration": str(duration),
            "transcript_file": final_transcript,
            "messages_count": len(transcript)
        }
    
    async def _run_agenda_item_discussion(self, agenda_item: str, participants: List[str], context: str) -> List[Dict]:
        """Run discussion for a specific agenda item"""
        discussion = []
        conversation_context = []
        
        # Each participant gets to speak initially
        for participant_key in participants:
            if participant_key not in self.agents:
                continue
                
            agent = self.agents[participant_key]
            
            # Build context for this agent
            prompt = self._build_meeting_prompt(agenda_item, conversation_context, context, agent.name)
            
            try:
                # Agent thinks and responds
                response = await agent.think(prompt)
                
                # Log to live meeting file
                await self._log_meeting_message(participant_key, agent.name, response)
                
                # Add to conversation context
                conversation_context.append({
                    "agent": participant_key,
                    "name": agent.name,
                    "emoji": agent.emoji,
                    "message": response
                })
                
                discussion.append({
                    "agent": participant_key,
                    "name": agent.name,
                    "emoji": agent.emoji,
                    "message": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                error_msg = f"Error getting response from {agent.name}: {str(e)}"
                await self._log_meeting_message("system", "📅 Meeting Facilitator", error_msg)
        
        # Follow-up discussion rounds
        for round_num in range(2):  # Allow 2 follow-up rounds
            follow_up_needed = await self._check_if_follow_up_needed(conversation_context, agenda_item)
            
            if not follow_up_needed:
                break
                
            # Agents can respond to each other
            for participant_key in participants:
                if participant_key not in self.agents:
                    continue
                    
                agent = self.agents[participant_key]
                
                # Check if this agent has something to add
                should_speak = await self._should_agent_speak(agent, conversation_context, agenda_item)
                
                if should_speak:
                    prompt = self._build_follow_up_prompt(agenda_item, conversation_context, agent.name)
                    
                    try:
                        response = await agent.think(prompt)
                        
                        if len(response.strip()) > 10:  # Only log substantial responses
                            await self._log_meeting_message(participant_key, agent.name, response)
                            
                            conversation_context.append({
                                "agent": participant_key,
                                "name": agent.name,
                                "emoji": agent.emoji,
                                "message": response
                            })
                            
                            discussion.append({
                                "agent": participant_key,
                                "name": agent.name,
                                "emoji": agent.emoji,
                                "message": response,
                                "timestamp": datetime.now().isoformat()
                            })
                    except Exception as e:
                        pass  # Skip errors in follow-up
        
        return discussion
    
    def _build_meeting_prompt(self, agenda_item: str, context: List[Dict], meeting_context: str, agent_name: str) -> str:
        """Build a prompt for an agent to participate in the meeting"""
        context_str = ""
        if context:
            context_str = "DISCUSSION SO FAR:\n"
            for msg in context[-5:]:  # Last 5 messages for context
                context_str += f"**{msg['name']}:** {msg['message']}\n\n"
        
        prompt = f"""You are participating in a team meeting.

MEETING CONTEXT: {meeting_context}
CURRENT AGENDA ITEM: {agenda_item}

{context_str}

As {agent_name}, provide your perspective on this agenda item. Be authentic to your role and personality:
- Share your professional opinion
- Raise concerns if you have them
- Suggest solutions or alternatives
- Debate points you disagree with
- Keep responses focused and concise (2-3 sentences max)

Your response should reflect your personality and expertise. Don't just agree - add value to the discussion."""
        
        return prompt
    
    def _build_follow_up_prompt(self, agenda_item: str, context: List[Dict], agent_name: str) -> str:
        """Build a follow-up prompt for continued discussion"""
        recent_context = ""
        for msg in context[-3:]:
            recent_context += f"**{msg['name']}:** {msg['message']}\n\n"
        
        prompt = f"""AGENDA ITEM: {agenda_item}

RECENT DISCUSSION:
{recent_context}

As {agent_name}, do you have a follow-up comment, concern, or suggestion based on what others have said?

Only respond if you have something meaningful to add. If you agree with what's been said, you can briefly acknowledge it. If you disagree or see issues, speak up!

Keep it brief (1-2 sentences)."""
        
        return prompt
    
    async def _should_agent_speak(self, agent: BaseAgent, context: List[Dict], agenda_item: str) -> bool:
        """Determine if an agent should speak in follow-up discussion"""
        # Simple heuristic: agents speak less frequently in follow-up
        import random
        
        # QA agent speaks more often (has veto power)
        if agent.key == "qa":
            return random.random() < 0.7
        
        # Architect speaks often on technical topics
        if agent.key == "architect" and any(word in agenda_item.lower() for word in ["architecture", "design", "technical"]):
            return random.random() < 0.8
        
        # General probability for follow-up
        return random.random() < 0.4
    
    async def _check_if_follow_up_needed(self, context: List[Dict], agenda_item: str) -> bool:
        """Check if more discussion is needed on this agenda item"""
        if len(context) < 2:
            return True
            
        # Look for disagreement or unresolved issues
        messages = [msg["message"].lower() for msg in context[-3:]]
        
        disagreement_indicators = ["but", "however", "disagree", "concern", "issue", "problem", "alternative"]
        return any(indicator in " ".join(messages) for indicator in disagreement_indicators)
    
    async def _log_meeting_message(self, agent_key: str, speaker_name: str, message: str):
        """Log message to live meeting file for real-time streaming"""
        agent_emoji = "📅"
        if agent_key in self.agents:
            agent_emoji = self.agents[agent_key].emoji
        elif agent_key == "system":
            agent_emoji = "📅"
            
        entry = {
            "ts": datetime.now().isoformat(),
            "agent": agent_key,
            "speaker": speaker_name,
            "emoji": agent_emoji,
            "text": message
        }
        
        # Append to live meeting file
        with open(self.live_meeting_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Small delay for realistic pacing
        await asyncio.sleep(0.5)
    
    async def _save_final_transcript(self, meeting_id: str, topic: str, participants: List[str], transcript: List[Dict], duration) -> str:
        """Save final meeting transcript as markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = f"meeting-{meeting_id}.md"
        filepath = self.meetings_dir / filename
        
        # Build markdown content
        lines = [
            f"# Meeting Transcript — {timestamp}",
            f"",
            f"**Topic:** {topic}",
            f"**Participants:** {', '.join(participants)}",
            f"**Duration:** {str(duration).split('.')[0]}",
            f"**Messages:** {len(transcript)}",
            f"",
            f"---",
            f""
        ]
        
        # Add transcript messages
        for entry in transcript:
            timestamp = entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
            except:
                ts = "00:00:00"
                
            lines.append(f"**[{ts}] {entry.get('emoji', '🤖')} {entry.get('name', 'Unknown')}:** {entry.get('message', '')}")
            lines.append("")
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        # Clean up live meeting file
        if self.live_meeting_file.exists():
            self.live_meeting_file.unlink()
        
        return filename