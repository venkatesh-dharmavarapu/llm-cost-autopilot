import os
import sqlite3
from datetime import datetime

DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "autopilot_metrics.db")

def get_db_connection():
    """Establishes a connection to the local SQLite database file."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    """Creates the analytics tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Core Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        prompt TEXT NOT NULL,
        routed_model TEXT NOT NULL,
        routing_tier TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        latency_seconds REAL NOT NULL,
        calculated_cost REAL NOT NULL
    )
    """)
    
    # Quality Audits and Escalations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quality_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        prompt TEXT NOT NULL,
        cheap_response TEXT NOT NULL,
        audit_score INTEGER NOT NULL,
        audit_reason TEXT NOT NULL,
        was_escalated INTEGER NOT NULL, -- 0 for False, 1 for True
        recovered_response TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def log_transaction_to_db(prompt: str, model_used: str, tier: str, input_t: int, output_t: int, latency: float, cost: float):
    """Inserts a standard API payload execution directly into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (timestamp, prompt, routed_model, routing_tier, input_tokens, output_tokens, latency_seconds, calculated_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat() + "Z", prompt, model_used, tier, input_t, output_t, latency, cost))
    conn.commit()
    conn.close()

def log_audit_to_db(prompt: str, cheap_response: str, score: int, reason: str, was_escalated: bool, recovered_text: str = None):
    """Inserts a background verification judge output and any recovery responses into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quality_audits (timestamp, prompt, cheap_response, audit_score, audit_reason, was_escalated, recovered_response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat() + "Z", prompt, cheap_response, score, reason, 1 if was_escalated else 0, recovered_text))
    conn.commit()
    conn.close()

# Initialize tables immediately upon importing this module
init_db()