import json
import re
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.models import MODEL_REGISTRY, send_request
from core.router import AutopilotRouter
# Import our clean Phase 4/5 SQLite Database layer
from core.database import log_transaction_to_db, log_audit_to_db

app = FastAPI(
    title="LLM Cost Autopilot API",
    description="Intelligent routing gateway integrated with an explicit SQLite metrics database ledger.",
    version="1.4.0"
)
router_engine = AutopilotRouter()

class PromptRequest(BaseModel):
    prompt: str

# --- Background Evaluator & Self-Healing Database Recovery ---
def verify_and_recover_response(prompt: str, cheap_model_response: str):
    print(f"\n[BACKGROUND EVALUATOR] Auditing cheap response for database logging...")
    
    judge_config = MODEL_REGISTRY.get("qwen-large")
    judge_prompt = f"""
You are an expert AI Quality Auditor. Your job is to grade the quality of a lightweight AI model's response compared to the original user intent.

[USER PROMPT]:
{prompt}

[LIGHTWEIGHT MODEL RESPONSE]:
{cheap_model_response}

Is the lightweight model's response accurate, safe, and helpful? Grade it strictly from 1 to 5 (where 5 is perfect and 1 is completely broken or unhelpful). 
Respond ONLY with a single raw JSON block containing your numerical 'score' and a one-sentence 'reason'. Do not wrap it in markdown text or use math formatting backslashes.
Example format: {{"score": 4, "reason": "The answer is accurate but missing slight context."}}
"""
    try:
        judge_receipt = send_request(judge_prompt, judge_config, tier="verification_judge")
        raw_output = judge_receipt.text.strip()
        
        clean_json_str = re.sub(r"```json\s*|\s*```", "", raw_output).strip()
        clean_json_str = clean_json_str.replace("\\(", "(").replace("\\)", ")")
        
        audit_data = json.loads(clean_json_str)
        score = int(audit_data.get("score", 5))
        reason = audit_data.get("reason", "")
        
        print(f"Parsed Score: {score}/5 | Reason: {reason}")
        
        was_escalated = False
        recovered_text = None
        
        if score <= 3:
            print(f"🚨 [CRITICAL ALERT] Quality threshold breached (Score: {score})!")
            print(f"🔄 [RECOVERY SYSTEM] Escalating prompt to 7B Master Model...")
            recovery_receipt = send_request(prompt, judge_config, tier="tier_3_fallback")
            recovered_text = recovery_receipt.text.strip()
            was_escalated = True
            print(f"✅ [RECOVERY COMPLETE] Fixed fallback response generated.")
        else:
            print(f"🛡️ [QUALITY SECURE] Tier 1 response validated securely.")

        # Save the full audit data safely into our SQLite quality_audits table
        log_audit_to_db(prompt, cheap_model_response, score, reason, was_escalated, recovered_text)
        print(f"💾 [SQLITE DATABASE] Quality audit ledger updated successfully.")
        print(f"--------------------------------")

    except Exception as e:
        print(f"[BACKGROUND ENGINE SQLITE ERROR] Audit table insert failed: {str(e)}")


# --- Main HTTP Completions Route ---
@app.post("/v1/completions")
async def handle_completion(payload: PromptRequest, background_tasks: BackgroundTasks):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Invalid request: Prompt content cannot be empty.")
    
    try:
        tier, designated_model_key = router_engine.route_request(payload.prompt)
        model_config = MODEL_REGISTRY.get(designated_model_key)
        
        execution_receipt = send_request(payload.prompt, model_config, tier)
        
        # Save completion logs into our local SQLite transactions table
        log_transaction_to_db(
            prompt=payload.prompt,
            model_used=execution_receipt.model_used,
            tier=execution_receipt.routing_tier,
            input_t=execution_receipt.input_tokens,
            output_t=execution_receipt.output_tokens,
            latency=execution_receipt.latency_seconds,
            cost=execution_receipt.calculated_cost
        )
        print(f"💾 [SQLITE DATABASE] Core transaction record committed to disk.")
        
        if tier == "tier_1":
            background_tasks.add_task(verify_and_recover_response, payload.prompt, execution_receipt.text)
        
        return execution_receipt

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "LLM Cost Autopilot Core"}