from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.models import MODEL_REGISTRY, send_request
from core.router import AutopilotRouter

# 1. Initialize the FastAPI application and our Routing Engine
app = FastAPI(
    title="LLM Cost Autopilot API",
    description="Intelligent routing gateway that optimizes LLM requests by task complexity.",
    version="1.0.0"
)
router_engine = AutopilotRouter()

# 2. Define the expected request shape using Pydantic
class PromptRequest(BaseModel):
    prompt: str

# 3. Create the Main Orchestration Endpoint
@app.post("/v1/completions")
async def handle_completion(payload: PromptRequest):
    """
    Accepts a universal prompt payload, dynamically classifies its complexity,
    routes it to the optimal local model, and returns a standardized response object.
    """
    # Defensive programming: ensure the user didn't send an empty prompt
    if not payload.prompt.strip():
        raise HTTPException(
            status_code=400, 
            detail="Invalid request: Prompt content cannot be empty."
        )
    
    try:
        # Step A: Run the text through our heuristic engine to determine the tier
        tier, designated_model_key = router_engine.route_request(payload.prompt)
        
        # Step B: Look up the model's configuration parameters from our registry
        model_config = MODEL_REGISTRY.get(designated_model_key)
        if not model_config:
            raise HTTPException(
                status_code=500, 
                detail="Routing Configuration Error: Target model config not found in registry."
            )
            
        # Step C: Dispatch the prompt to the selected model and capture the standardized receipt
        execution_receipt = send_request(payload.prompt, model_config, tier)
        
        return execution_receipt

    except Exception as e:
        # Gracefully handle unexpected connection issues or runtime failures
        raise HTTPException(status_code=500, detail=str(e))

# 4. Built-in health check to confirm the API service is up and running
@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "LLM Cost Autopilot Core"}