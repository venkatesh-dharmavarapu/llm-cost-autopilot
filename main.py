from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.models import MODEL_REGISTRY, send_request
from core.router import AutopilotRouter

app = FastAPI(
    title="LLM Cost Autopilot API",
    description="Intelligent routing gateway with background evaluation loops.",
    version="1.1.0"
)
router_engine = AutopilotRouter()

class PromptRequest(BaseModel):
    prompt: str

# --- Phase 3 Feature: Background Quality Evaluator (LLM-as-a-Judge) ---
def verify_response_quality(prompt: str, cheap_model_response: str):
    """
    Runs completely in the background. It asks our heavy-duty 7B model 
    to audit the output of our tiny 1.5B model and score it.
    """
    print(f"\n[BACKGROUND EVALUATOR] Auditing cheap response for quality verification...")
    
    # Target our smart 7B model to act as our auditor
    judge_config = MODEL_REGISTRY.get("qwen-large")
    
    judge_prompt = f"""
You are an expert AI Quality Auditor. Your job is to grade the quality of a lightweight AI model's response compared to the original user intent.

[USER PROMPT]:
{prompt}

[LIGHTWEIGHT MODEL RESPONSE]:
{cheap_model_response}

Is the lightweight model's response accurate, safe, and helpful? Grade it strictly from 1 to 5 (where 5 is perfect and 1 is completely broken or unhelpful). 
Respond ONLY with a single JSON block containing your numerical 'score' and a one-sentence 'reason'. 
Example format: {{"score": 4, "reason": "The answer is accurate but missing slight context."}}
"""
    try:
        # Send the audit prompt to our local 7B model
        judge_receipt = send_request(judge_prompt, judge_config, tier="verification_judge")
        print(f"--- [AUDIT REPORT COMPLETED] ---")
        print(f"Judge Output:\n{judge_receipt.text.strip()}")
        print(f"--------------------------------")
    except Exception as e:
        print(f"[BACKGROUND ENGINE ERROR] Verification failed: {str(e)}")


# --- Main HTTP Completions Route ---
@app.post("/v1/completions")
async def handle_completion(payload: PromptRequest, background_tasks: BackgroundTasks):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Invalid request: Prompt content cannot be empty.")
    
    try:
        # 1. Determine the model to use based on prompt complexity
        tier, designated_model_key = router_engine.route_request(payload.prompt)
        model_config = MODEL_REGISTRY.get(designated_model_key)
        
        # 2. Get our immediate answer from the selected model
        execution_receipt = send_request(payload.prompt, model_config, tier)
        
        # 3. PHASE 3 CRITICAL TRICK: If we used the cheap model (tier_1), 
        # queue up the async background task to verify it without keeping the user waiting!
        if tier == "tier_1":
            background_tasks.add_task(
                verify_response_quality, 
                payload.prompt, 
                execution_receipt.text
            )
        
        return execution_receipt

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "LLM Cost Autopilot Core"}