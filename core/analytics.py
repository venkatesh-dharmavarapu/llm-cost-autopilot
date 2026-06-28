import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Define the path for our system logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "autopilot_metrics.log")

# Setup a professional rotating file logger (Max 5MB per file, keeps 3 backups)
logger = logging.getLogger("LLM_Autopilot_Analytics")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def log_completion_metrics(receipt_dict: dict):
    """
    Formats and appends clean API completion transactions into a structured analytics log.
    """
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "transaction_completion",
        "model_used": receipt_dict.get("model_used"),
        "routing_tier": receipt_dict.get("routing_tier"),
        "input_tokens": receipt_dict.get("input_tokens", 0),
        "output_tokens": receipt_dict.get("output_tokens", 0),
        "latency_seconds": receipt_dict.get("latency_seconds", 0.0),
        "estimated_cost": receipt_dict.get("calculated_cost", 0.0)
    }
    # Log as structured JSON string for easy parsing by data tools
    logger.info(json.dumps(payload))

def log_audit_metrics(score: int, reason: str, was_recovered: bool):
    """
    Formats and logs background LLM-as-a-Judge quality metrics and system corrections.
    """
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "quality_audit",
        "audit_score": score,
        "audit_reason": reason,
        "action_taken": "fallback_recovery_triggered" if was_recovered else "passed_threshold"
    }
    logger.info(json.dumps(payload))