"""
Frontend Agent - Frankie 🎨
UI/UX Implementation Specialist
"""
from .base import BaseAgent
from typing import Dict, List

class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Frankie",
            emoji="🎨",
            role="UI/UX Implementation Specialist", 
            role_file="frontend.md"
        )
    
    async def implement_ui(self, task: Dict, design_specs: Dict) -> Dict:
        """Implement UI components and screens"""
        prompt = f"""
        TASK: {task}
        DESIGN SPECIFICATIONS: {design_specs}
        
        As the frontend specialist, implement this UI feature.
        Focus on:
        - User experience and usability
        - Responsive design
        - Accessibility
        - Performance
        - Component reusability
        
        Return implementation in JSON format:
        {{
            "components": [
                {{
                    "path": "components/ComponentName.jsx", 
                    "content": "component code"
                }}
            ],
            "screens": [
                {{
                    "path": "screens/ScreenName.jsx",
                    "content": "screen code"
                }}
            ],
            "styles": [
                {{
                    "path": "styles/component-styles.css",
                    "content": "CSS styles"
                }}
            ],
            "summary": "implementation summary",
            "ux_notes": ["important UX considerations and decisions"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def review_ux(self, feature: Dict) -> Dict:
        """Review feature from UX perspective"""
        prompt = f"""
        FEATURE TO REVIEW: {feature}
        
        Review this feature from a user experience perspective:
        - Is the user flow intuitive?
        - Are there usability issues?
        - Is it accessible to all users?
        - Does it work well on mobile?
        - Are error states handled well?
        
        Return your UX review:
        {{
            "ux_score": "1-10 rating",
            "usability_issues": ["list of usability problems"],
            "accessibility_issues": ["accessibility concerns"], 
            "mobile_issues": ["mobile-specific problems"],
            "suggestions": ["improvement suggestions"],
            "user_flow_feedback": "feedback on the user journey"
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def optimize_performance(self, code: Dict) -> Dict:
        """Optimize frontend performance"""
        prompt = f"""
        FRONTEND CODE TO OPTIMIZE: {code}
        
        Analyze and optimize this frontend code for performance:
        - Loading times
        - Render performance
        - Memory usage
        - Bundle size
        - User perceived performance
        
        Return optimization suggestions:
        {{
            "optimizations": [
                {{
                    "type": "loading|rendering|memory|bundle",
                    "description": "what to optimize",
                    "implementation": "how to implement the optimization"
                }}
            ],
            "performance_impact": "expected impact on user experience",
            "priority": "high|medium|low"
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def suggest_improvements(self, current_ui: Dict) -> Dict:
        """Suggest UI/UX improvements"""
        prompt = f"""
        CURRENT UI: {current_ui}
        
        As the UX specialist, suggest improvements to make this interface better:
        - User experience enhancements
        - Visual design improvements
        - Accessibility improvements
        - Mobile experience improvements
        - Animation and interaction improvements
        
        Return your suggestions:
        {{
            "ux_improvements": ["user experience enhancements"],
            "visual_improvements": ["visual design suggestions"],
            "accessibility_improvements": ["accessibility enhancements"],
            "mobile_improvements": ["mobile-specific improvements"],
            "interaction_improvements": ["animation and interaction suggestions"],
            "priority_order": ["list improvements by priority"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    def _extract_json(self, response: str, default_value: Dict = None) -> Dict:
        """Extract JSON from response text"""
        import json
        
        if default_value is None:
            default_value = {"summary": "Frontend task completed"}
            
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
                
        except (json.JSONDecodeError, ValueError):
            pass
        
        return default_value