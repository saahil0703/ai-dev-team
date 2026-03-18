"""
Backend Agent - Blake ⚙️
API, Database & Business Logic Specialist
"""
from .base import BaseAgent
from typing import Dict, List

class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Blake", 
            emoji="⚙️",
            role="API, Database & Business Logic Specialist",
            role_file="backend.md"
        )
    
    async def design_api(self, requirements: Dict) -> Dict:
        """Design API endpoints and data contracts"""
        prompt = f"""
        REQUIREMENTS: {requirements}
        
        Design the API endpoints and data contracts for these requirements.
        Consider:
        - RESTful design principles
        - Data validation
        - Authentication/authorization
        - Error handling
        - Performance considerations
        
        Return API design in JSON format:
        {{
            "endpoints": [
                {{
                    "method": "GET|POST|PUT|DELETE",
                    "path": "/api/endpoint",
                    "description": "what this endpoint does",
                    "request_body": {{"field": "type and description"}},
                    "response": {{"field": "type and description"}},
                    "authentication": "required|optional|none"
                }}
            ],
            "data_models": [
                {{
                    "name": "ModelName",
                    "fields": {{"field_name": "type and constraints"}},
                    "relationships": ["related models"]
                }}
            ],
            "security_considerations": ["authentication and authorization notes"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def implement_backend(self, task: Dict, api_design: Dict) -> Dict:
        """Implement backend functionality"""
        prompt = f"""
        TASK: {task}
        API DESIGN: {api_design}
        
        Implement the backend functionality for this task.
        Focus on:
        - Clean, maintainable code
        - Proper error handling
        - Security best practices
        - Database optimization
        - Input validation
        
        Return implementation files:
        {{
            "api_routes": [
                {{
                    "path": "routes/endpoint.py",
                    "content": "route handler code"
                }}
            ],
            "models": [
                {{
                    "path": "models/ModelName.py", 
                    "content": "data model code"
                }}
            ],
            "services": [
                {{
                    "path": "services/service.py",
                    "content": "business logic service code"
                }}
            ],
            "database": [
                {{
                    "path": "migrations/001_create_tables.sql",
                    "content": "database migration"
                }}
            ],
            "tests": [
                {{
                    "path": "tests/test_endpoint.py",
                    "content": "test code"
                }}
            ],
            "summary": "implementation summary"
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def optimize_performance(self, code: Dict) -> Dict:
        """Optimize backend performance"""
        prompt = f"""
        BACKEND CODE TO OPTIMIZE: {code}
        
        Analyze and optimize this backend code for performance:
        - Database query optimization
        - Caching strategies
        - API response times
        - Memory usage
        - Concurrency handling
        
        Return optimization recommendations:
        {{
            "database_optimizations": ["query and schema optimizations"],
            "caching_strategy": ["caching recommendations"],
            "api_optimizations": ["API performance improvements"],
            "concurrency_improvements": ["async/parallel processing suggestions"],
            "monitoring_suggestions": ["what to monitor in production"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def review_security(self, code: Dict) -> Dict:
        """Review code for security vulnerabilities"""
        prompt = f"""
        CODE TO REVIEW: {code}
        
        Review this backend code for security vulnerabilities:
        - Input validation and sanitization
        - SQL injection prevention
        - Authentication and authorization
        - Data encryption
        - API security best practices
        
        Return security assessment:
        {{
            "security_score": "1-10 rating",
            "vulnerabilities": [
                {{
                    "severity": "high|medium|low",
                    "description": "vulnerability description",
                    "fix": "how to fix it"
                }}
            ],
            "security_recommendations": ["general security improvements"],
            "compliance_notes": ["regulatory compliance considerations"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def design_database(self, requirements: Dict) -> Dict:
        """Design database schema"""
        prompt = f"""
        REQUIREMENTS: {requirements}
        
        Design the database schema for these requirements.
        Consider:
        - Data relationships and normalization
        - Indexes for performance
        - Constraints and validation
        - Scalability requirements
        
        Return database design:
        {{
            "tables": [
                {{
                    "name": "table_name",
                    "columns": [
                        {{
                            "name": "column_name",
                            "type": "data_type",
                            "constraints": ["NOT NULL", "UNIQUE", etc],
                            "description": "what this column stores"
                        }}
                    ],
                    "indexes": ["list of indexes"],
                    "relationships": ["foreign key relationships"]
                }}
            ],
            "migrations": ["list of migration steps"],
            "performance_considerations": ["performance optimization notes"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    def _extract_json(self, response: str, default_value: Dict = None) -> Dict:
        """Extract JSON from response text"""
        import json
        
        if default_value is None:
            default_value = {"summary": "Backend task completed"}
            
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