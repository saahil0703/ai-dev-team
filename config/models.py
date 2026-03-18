"""
AI Model configuration for different agents
"""
import os

# Default model
DEFAULT_MODEL = os.getenv("AGENT_MODEL", "claude-sonnet-4-20250514")

# Per-agent model configuration
AGENT_MODELS = {
    "architect": os.getenv("ARCHITECT_MODEL", DEFAULT_MODEL),
    "frontend": os.getenv("FRONTEND_MODEL", DEFAULT_MODEL), 
    "backend": os.getenv("BACKEND_MODEL", DEFAULT_MODEL),
    "qa": os.getenv("QA_MODEL", DEFAULT_MODEL),
    "meeting": os.getenv("MEETING_MODEL", DEFAULT_MODEL),
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL),
}

# Model capabilities and limits
MODEL_CONFIGS = {
    "claude-sonnet-4-20250514": {
        "max_tokens": 8192,
        "context_window": 200000,
        "good_for": ["general", "coding", "reasoning"],
        "cost_tier": "mid"
    },
    "claude-opus-4-6": {
        "max_tokens": 4096,
        "context_window": 200000,
        "good_for": ["complex_reasoning", "architecture", "planning"],
        "cost_tier": "high"
    },
    "claude-haiku-4-20241224": {
        "max_tokens": 4096,
        "context_window": 200000,
        "good_for": ["simple_tasks", "formatting", "quick_responses"],
        "cost_tier": "low"
    }
}

def get_model_for_agent(agent_key: str) -> str:
    """Get the configured model for a specific agent"""
    return AGENT_MODELS.get(agent_key, DEFAULT_MODEL)

def get_model_config(model_name: str) -> dict:
    """Get configuration for a specific model"""
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS[DEFAULT_MODEL])