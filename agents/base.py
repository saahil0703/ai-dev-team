"""
Base Agent class for all AI agents in the dev team platform
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import anthropic
from config.models import get_model_for_agent, get_model_config

class BaseAgent:
    def __init__(self, name: str, emoji: str, role: str, role_file: str):
        """Initialize the base agent with core configuration"""
        self.name = name
        self.emoji = emoji
        self.role = role
        self.key = role_file.split('.')[0]  # e.g. 'architect' from 'architect.md'
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Get model configuration for this agent
        self.model = get_model_for_agent(self.key)
        self.model_config = get_model_config(self.model)
        
        # Conversation history
        self.conversation = []
        
        # Load role prompt from roles file
        self.system_prompt = self._load_role_prompt(role_file)
        
    def _load_role_prompt(self, role_file: str) -> str:
        """Load the role prompt from the roles directory"""
        role_path = Path(__file__).parent / "roles" / role_file
        if role_path.exists():
            return role_path.read_text()
        else:
            return f"You are {self.name} ({self.emoji}), a {self.role} agent in an AI development team."
    
    async def think(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Core thinking method - calls Anthropic API with role system prompt
        """
        try:
            # Prepare context information
            context_str = ""
            if context:
                context_str = f"\n\n**Context:**\n{json.dumps(context, indent=2)}"
            
            # Build full prompt with role context
            full_prompt = f"{prompt}{context_str}"
            
            # Add to conversation history
            self.conversation.append({"role": "user", "content": full_prompt})
            
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.model_config.get("max_tokens", 4096),
                system=self.system_prompt,
                messages=self.conversation[-10:]  # Keep last 10 exchanges for context
            )
            
            # Extract response text
            response_text = response.content[0].text if response.content else "No response"
            
            # Add response to conversation history
            self.conversation.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error in {self.name} thinking: {str(e)}"
            print(error_msg)
            return error_msg
    
    async def code(self, task: str, project_context: Dict) -> Dict:
        """
        Generate code files for a given task
        Returns: {files: [{path, content}], summary}
        """
        prompt = f"""
        TASK: {task}
        
        PROJECT CONTEXT:
        {json.dumps(project_context, indent=2)}
        
        Generate the necessary code files for this task. Return your response in this JSON format:
        {{
            "files": [
                {{"path": "relative/path/to/file.ext", "content": "file content here"}},
                ...
            ],
            "summary": "Brief description of what was implemented"
        }}
        
        Focus on clean, production-ready code that follows best practices for the tech stack.
        """
        
        response = await self.think(prompt, project_context)
        
        try:
            # Try to extract JSON from response
            # Look for JSON block in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback if JSON parsing fails
        return {
            "files": [],
            "summary": f"Code generation completed by {self.name}",
            "raw_response": response
        }
    
    async def review(self, code: Dict, criteria: str) -> Dict:
        """
        Review code against given criteria
        Returns: {approved: bool, feedback: str, bugs: List[str]}
        """
        prompt = f"""
        REVIEW CRITERIA: {criteria}
        
        CODE TO REVIEW:
        {json.dumps(code, indent=2)}
        
        Please review this code and return your assessment in this JSON format:
        {{
            "approved": true/false,
            "feedback": "Detailed feedback on the code quality and implementation",
            "bugs": ["List of specific bugs or issues found"],
            "suggestions": ["List of improvement suggestions"]
        }}
        
        Be thorough in your review. Focus on correctness, best practices, security, and maintainability.
        """
        
        response = await self.think(prompt)
        
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback if JSON parsing fails
        return {
            "approved": False,
            "feedback": response,
            "bugs": [],
            "suggestions": []
        }
    
    def reset_conversation(self):
        """Reset conversation history (useful for new sessions)"""
        self.conversation = []
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "name": self.name,
            "emoji": self.emoji,
            "role": self.role,
            "model": self.model,
            "conversation_length": len(self.conversation),
            "active": len(self.conversation) > 0
        }