import streamlit as st
import sqlite3
import pandas as pd
import os
import requests

DB_FILE = os.path.join("data", "autopilot_metrics.db")
API_URL = "http://localhost:8000/v1/completions"

st.set_page_config(page_title="LLM Cost Autopilot Admin", layout="wide")

st.title("📊 LLM Cost Autopilot Analytics Dashboard")
st.markdown("Real-time telemetry, model distribution ratios, and infrastructure financial optimization analytics.")

st.markdown("---")

# --- NEW EXTENSION: LIVE ROUTER PLAYGROUND CHAT BOX ---
st.subheader("💬 Live Router Playground")
st.markdown("Type a prompt below to send it to your live FastAPI gateway. The gateway will automatically classify, route, and log the transaction metrics instantly.")

# Create a clean border box layout for the chat interface
with st.container(border=True):
    user_prompt = st.text_input("Enter your prompt / question:", placeholder="e.g., Write a python function to reverse a string...")
    submit_button = st.button("Send Prompt to Autopilot", use_container_width=True)
    
    if submit_button and user_prompt.strip():
        with st.spinner("Autopilot gateway routing request..."):
            try:
                # Send the POST request exactly like Invoke-RestMethod did
                response = requests.post(API_URL, json={"prompt": user_prompt.strip()})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("🎉 Response Received Successfully!")
                    
                    # Create columns to display the model routing metadata beautifully
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    with meta_col1:
                        st.info(f"**Model Selected:** {data.get('model_used')}")
                    with meta_col2:
                        st.info(f"**Routing Tier:** {data.get('routing_tier')}")
                    with meta_col3:
                        st.info(f"**Latency:** {data.get('latency_seconds'):.3f}s")
                    
                    # Display the actual text output inside a clean markdown block
                    st.markdown("### 🤖 Output Text:")
                    st.code(data.get("text"), language="markdown")
                else:
                    st.error(f"Gateway returned an error code: {response.status_code}")
            except Exception as e:
                st.error(f"Could not connect to FastAPI gateway. Is your uvicorn server running? Error: {str(e)}")

st.markdown("---")

# --- Database Reader Helper Functions ---
def load_transaction_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

def load_audit_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM quality_audits", conn)
    conn.close()
    return df

df_tx = load_transaction_data()
df_aud = load_audit_data()

if df_tx.empty:
    st.warning("⚠️ No database transaction metrics recorded yet. Send API requests using the box above to populate the dashboard.")
else:
    # --- CALCULATE THE BLUEPRINT MONEY SHOT METRIC ---
    total_input_tokens = df_tx["input_tokens"].sum()
    total_output_tokens = df_tx["output_tokens"].sum()
    
    hypothetical_unoptimized_cost = ((total_input_tokens / 1_000_000) * 5.00) + ((total_output_tokens / 1_000_000) * 15.00)
    actual_local_cost = df_tx["calculated_cost"].sum()
    
    money_saved = max(0.0, hypothetical_unoptimized_cost - actual_local_cost)
    savings_percentage = 100.0 if hypothetical_unoptimized_cost > 0 else 0.0

    # --- Metrics Top Row Cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Routed Requests", value=len(df_tx))
    with col2:
        st.metric(label="Average System Latency", value=f"{df_tx['latency_seconds'].mean():.2f}s")
    with col3:
        st.metric(label="Calculated Infrastructure Savings", value=f"${money_saved:.4f}")
    with col4:
        st.metric(label="🔥 THE MONEY SHOT (Cost Reduction)", value=f"{savings_percentage:.1f}%")

    st.markdown("---")

    # --- Charts Middle Row layout ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🤖 Model Traffic Distribution")
        model_counts = df_tx["routed_model"].value_counts()
        st.bar_chart(model_counts)
        
    with chart_col2:
        st.subheader("📈 System Latency Timeline (Seconds)")
        st.line_chart(df_tx["latency_seconds"])

    st.markdown("---")

    # --- Raw Audit Log Explorer Bottom Row ---
    st.subheader("🕵️ LLM-As-A-Judge Quality Audit Ledger")
    if not df_aud.empty:
        st.dataframe(df_aud[["timestamp", "audit_score", "audit_reason", "was_escalated"]], use_container_width=True)
    else:
        st.info("No background quality audits recorded yet.")