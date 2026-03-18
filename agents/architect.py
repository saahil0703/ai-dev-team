"""
Architect Agent - Alex 🏗️
System Designer & Technical Lead
"""
from .base import BaseAgent
from typing import Dict, List

class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Alex",
            emoji="🏗️", 
            role="System Designer & Technical Lead",
            role_file="architect.md"
        )
    
    async def design_system(self, requirements: Dict) -> Dict:
        """Design system architecture from requirements"""
        prompt = f"""
        PRODUCT REQUIREMENTS:
        {requirements}
        
        As the system architect, design the technical architecture for this project.
        Provide your response in JSON format:
        
        {{
            "tech_stack": {{
                "frontend": "framework choice with reasoning",
                "backend": "framework choice with reasoning", 
                "database": "database choice with reasoning",
                "deployment": "deployment strategy"
            }},
            "architecture": {{
                "data_models": ["list of main entities"],
                "api_structure": ["main API endpoints/patterns"],
                "file_structure": "proposed directory structure",
                "key_decisions": ["important architectural decisions"]
            }},
            "considerations": {{
                "scalability": "how the system will scale",
                "security": "key security considerations",
                "performance": "performance optimization strategy"
            }}
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def break_down_sprint(self, project_context: Dict, goals: List[str]) -> List[Dict]:
        """Break down sprint goals into specific tasks"""
        prompt = f"""
        PROJECT CONTEXT:
        {project_context}
        
        SPRINT GOALS:
        {goals}
        
        As the architect, break these sprint goals into specific, actionable tasks.
        Return a JSON array of tasks:
        
        [
            {{
                "id": "T-001",
                "title": "Clear, specific task title",
                "description": "Detailed task description with acceptance criteria",
                "assignee": "backend|frontend|qa",
                "priority": "critical|high|medium|low",
                "estimated_duration": "estimated time to complete",
                "dependencies": ["list of task IDs this depends on"],
                "acceptance_criteria": ["clear criteria for completion"]
            }}
        ]
        
        Consider dependencies, complexity, and which agent is best suited for each task.
        """
        
        response = await self.think(prompt)
        return self._extract_json(response, default_value=[])
    
    async def review_architecture(self, code_changes: Dict) -> Dict:
        """Review code changes for architectural compliance"""
        prompt = f"""
        CODE CHANGES TO REVIEW:
        {code_changes}
        
        Review these changes from an architectural perspective:
        - Do they follow established patterns?
        - Do they introduce technical debt?
        - Are they scalable and maintainable?
        - Do they violate any architectural principles?
        
        Return your review in JSON format:
        {{
            "approved": true/false,
            "feedback": "detailed architectural feedback",
            "concerns": ["list of architectural concerns"],
            "suggestions": ["improvement suggestions"],
            "technical_debt": ["potential tech debt issues"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    def _extract_json(self, response: str, default_value: Dict = None) -> Dict:
        """Extract JSON from response text"""
        import json
        
        if default_value is None:
            default_value = {}
            
        try:
            # Find JSON in response
            start = response.find('{') if '{' in response else response.find('[')
            end = response.rfind('}') + 1 if '}' in response else response.rfind(']') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
                
        except (json.JSONDecodeError, ValueError):
            pass
        
        return default_value