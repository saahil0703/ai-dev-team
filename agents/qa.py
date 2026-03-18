"""
QA Agent - Quinn 🔍
Quality Assurance & Testing Specialist
"""
from .base import BaseAgent
from typing import Dict, List

class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Quinn",
            emoji="🔍", 
            role="Quality Assurance & Testing Specialist",
            role_file="qa.md"
        )
    
    async def create_test_plan(self, feature: Dict) -> Dict:
        """Create comprehensive test plan for a feature"""
        prompt = f"""
        FEATURE TO TEST: {feature}
        
        Create a comprehensive test plan for this feature.
        Think like a real user and consider edge cases:
        - Happy path testing
        - Error scenarios
        - Edge cases and boundary conditions
        - User experience testing
        - Cross-platform compatibility
        
        Return test plan in JSON format:
        {{
            "test_cases": [
                {{
                    "id": "TC-001",
                    "title": "test case title",
                    "description": "what to test",
                    "steps": ["step 1", "step 2", "step 3"],
                    "expected_result": "what should happen",
                    "priority": "critical|high|medium|low",
                    "category": "functional|usability|security|performance"
                }}
            ],
            "edge_cases": ["list of edge cases to test"],
            "user_scenarios": ["real-world user scenarios to validate"],
            "compatibility_requirements": ["platforms/browsers to test on"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def test_feature(self, feature: Dict, test_plan: Dict) -> Dict:
        """Execute testing and find bugs"""
        prompt = f"""
        FEATURE: {feature}
        TEST PLAN: {test_plan}
        
        Execute thorough testing of this feature as a QA specialist.
        Look for:
        - Functional bugs
        - Usability issues
        - Performance problems
        - Security vulnerabilities
        - Accessibility issues
        
        Return testing results:
        {{
            "test_results": [
                {{
                    "test_case_id": "TC-001",
                    "status": "pass|fail|blocked",
                    "notes": "testing notes and observations"
                }}
            ],
            "bugs_found": [
                {{
                    "id": "BUG-001",
                    "severity": "critical|high|medium|low",
                    "title": "bug title",
                    "description": "detailed bug description",
                    "steps_to_reproduce": ["step 1", "step 2", "step 3"],
                    "expected_behavior": "what should happen",
                    "actual_behavior": "what actually happens",
                    "category": "functional|ui|performance|security"
                }}
            ],
            "usability_issues": ["user experience problems found"],
            "overall_quality": "assessment of feature quality",
            "ready_for_release": true/false
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def review_release(self, sprint_features: List[Dict]) -> Dict:
        """Review entire sprint for release readiness"""
        prompt = f"""
        SPRINT FEATURES FOR RELEASE: {sprint_features}
        
        As the QA lead, review all features for release readiness.
        Consider:
        - Are all critical bugs fixed?
        - Is the user experience acceptable?
        - Are there any regressions?
        - Is the feature set coherent and complete?
        
        Make a GO/NO-GO decision for release:
        {{
            "release_decision": "GO|NO-GO",
            "decision_reasoning": "detailed reasoning for the decision",
            "blocking_issues": ["issues that must be fixed before release"],
            "quality_score": "1-10 overall quality rating",
            "user_impact_assessment": "how will this affect users",
            "risk_assessment": "what could go wrong",
            "recommendations": ["what to do before releasing"]
        }}
        
        Remember: You have VETO POWER. Don't approve releases that aren't truly ready for users.
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def verify_bug_fix(self, bug: Dict, fix: Dict) -> Dict:
        """Verify that a bug fix actually works"""
        prompt = f"""
        ORIGINAL BUG: {bug}
        PROPOSED FIX: {fix}
        
        Verify that this bug fix actually resolves the issue:
        - Does it fix the reported problem?
        - Does it introduce any new issues?
        - Are the reproduction steps now working?
        - Are there any edge cases still broken?
        
        Return verification results:
        {{
            "fix_verified": true/false,
            "verification_notes": "detailed notes about testing the fix",
            "regression_testing": ["additional areas tested for regressions"],
            "new_issues": ["any new problems introduced by the fix"],
            "status": "fixed|not_fixed|partially_fixed",
            "recommendation": "what should happen next"
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    async def accessibility_review(self, feature: Dict) -> Dict:
        """Review feature for accessibility compliance"""
        prompt = f"""
        FEATURE FOR ACCESSIBILITY REVIEW: {feature}
        
        Review this feature for accessibility compliance:
        - Keyboard navigation
        - Screen reader compatibility
        - Color contrast
        - WCAG 2.1 compliance
        - Mobile accessibility
        
        Return accessibility assessment:
        {{
            "accessibility_score": "1-10 rating",
            "wcag_compliance": "AA|A|non-compliant",
            "accessibility_issues": [
                {{
                    "severity": "critical|high|medium|low",
                    "issue": "description of accessibility problem",
                    "impact": "which users are affected",
                    "solution": "how to fix it"
                }}
            ],
            "keyboard_navigation": "assessment of keyboard accessibility",
            "screen_reader_compatibility": "assessment of screen reader support",
            "recommendations": ["accessibility improvement suggestions"]
        }}
        """
        
        response = await self.think(prompt)
        return self._extract_json(response)
    
    def _extract_json(self, response: str, default_value: Dict = None) -> Dict:
        """Extract JSON from response text"""
        import json
        
        if default_value is None:
            default_value = {"summary": "QA task completed"}
            
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