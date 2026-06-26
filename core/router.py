# 1. Map our abstract tiers directly to our registry keys
DEFAULT_ROUTING_MAP = {
    "tier_1": "qwen-tiny",   # Simple tasks (e.g., formatting, basic queries)
    "tier_2": "qwen-tiny",   # Moderate tasks 
    "tier_3": "qwen-large"   # Complex reasoning, code generation, heavy logic
}

class HeuristicClassifier:
    """Analyzes string features to classify prompt complexity into specific tiers."""
    
    def predict_tier(self, prompt: str) -> str:
        # Step A: Check word count (Length is a massive indicator of context complexity)
        word_count = len(prompt.split())
        
        # Step B: Check for heavy algorithmic or analytical triggers
        # Since we are using coder models, these keywords represent high-complexity requests
        complex_triggers = [
            "analyze", "compare", "optimize", "evaluate", "explain step-by-step",
            "write a class", "debug", "architect", "refactor", "implement"
        ]
        
        prompt_lower = prompt.lower()
        
        # If it's a long prompt or explicitly asks for deep engineering work, push to Tier 3
        if word_count > 150 or any(trigger in prompt_lower for trigger in complex_triggers):
            return "tier_3"
        
        # Otherwise, keep it cheap and fast on Tier 1
        return "tier_1"

class AutopilotRouter:
    """The master orchestrator that classifies requests and matches them to models."""
    
    def __init__(self):
        self.classifier = HeuristicClassifier()
        self.routing_map = DEFAULT_ROUTING_MAP
        
    def route_request(self, prompt: str):
        """Returns a tuple of (tier_name, model_registry_key)"""
        tier = self.classifier.predict_tier(prompt)
        assigned_model = self.routing_map.get(tier, "qwen-tiny")
        return tier, assigned_model