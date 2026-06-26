import time
import requests
from pydantic import BaseModel

# 1. Model Configuration Registry Structure
class ModelConfig(BaseModel):
    provider: str          # For our setup, this will always be "ollama"
    model_id: str          # The exact Ollama model identifier (e.g., "qwen2.5-coder:1.5b")
    cost_per_input_token: float   # 0.0 since it's local, but great for architectural parity
    cost_per_output_token: float  # 0.0 since it's local
    quality_tier: str      # "high", "medium", or "low"

# 2. Standardized Response Object
class RouterResponse(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    calculated_cost: float
    model_used: str
    routing_tier: str

# 3. Populate Our Local Model Registry
MODEL_REGISTRY = {
    "qwen-tiny": ModelConfig(
        provider="ollama",
        model_id="qwen2.5-coder:1.5b",
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        quality_tier="low"
    ),
    "qwen-large": ModelConfig(
        provider="ollama",
        model_id="qwen2.5-coder:7b",
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        quality_tier="high"
    ),
}

# 4. The Unified Request Controller
def send_request(prompt: str, config: ModelConfig, tier: str) -> RouterResponse:
    """Handles the communication with Ollama and returns a unified Response data object."""
    start_time = time.time()
    
    try:
        # Send an HTTP POST request to your locally running Ollama server
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": config.model_id,
                "prompt": prompt,
                "stream": False  # We want the full text back at once, not streamed token-by-token
            },
            timeout=120
        )
        response.raise_for_status()  # Crash gracefully if Ollama returns an error code
        data = response.json()
        
        text_out = data.get("response", "")
        
        # Ollama explicitly tracks native tokens used during processing
        in_tokens = data.get("prompt_eval_count", 0)
        out_tokens = data.get("eval_count", 0)
        
        latency = time.time() - start_time
        cost = (in_tokens * config.cost_per_input_token) + (out_tokens * config.cost_per_output_token)

        # Map everything neatly into our strict Pydantic structure
        return RouterResponse(
            text=text_out,
            input_tokens=int(in_tokens),
            output_tokens=int(out_tokens),
            latency_seconds=round(latency, 3),
            calculated_cost=round(cost, 6),
            model_used=config.model_id,
            routing_tier=tier
        )
    except Exception as e:
        raise RuntimeError(f"Failed communicating with Ollama model {config.model_id}: {str(e)}")