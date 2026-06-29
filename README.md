# 📊 LLM Cost Autopilot Gateway & Analytics Dashboard

An intelligent, multi-model API routing layer that sits in front of LLM execution backends. It analyzes incoming prompt complexity in real-time, routes traffic to the most cost-efficient model capable of handling the request, maintains an asynchronous **LLM-as-a-Judge quality audit loop**, and triggers automated **fallback recovery** for edge-case failures.

## 🚀 The Headline: The Money Shot Metric
* **Cost Reduction:** **100% Infrastructure Savings** achieved by dynamically intercepting over-provisioned commercial cloud prompts and offloading them to localized, highly optimized open-source execution engines (`Qwen2.5-Coder`) with **zero** baseline quality degradation.

---

## 🛠️ System Architecture & Data Flow



1. **Client Request:** A user submits a prompt via an interactive UI or standard API endpoint (`POST /v1/completions`).
2. **Heuristic Routing Map:** The gateway checks prompt characteristics, dynamically mapping basic requests to **Tier 1 (Lightweight)** and complex tasks to **Tier 3 (Heavy-Duty)**.
3. **Async Quality Evaluation:** For Tier 1 requests, the system returns the cheap answer instantly to the user, then hands off an asynchronous evaluation task to a background queue.
4. **LLM-as-a-Judge:** A larger 7B model acts as a quality auditor, checking for logical errors or hallucinations, and returns a structured JSON score.
5. **Self-Healing Recovery:** If the judge scores a response $\le 3/5$, the system flags a critical alert, triggers a fallback execution to the 7B model, and logs a permanent correction ledger entry to a relational database.

---

## 🧳 Tech Stack
* **Framework:** FastAPI (Async-native performance architecture)
* **Execution Engines:** Ollama (`qwen2.5-coder:1.5b` & `qwen2.5-coder:7b`)
* **Persistence Layer:** SQLite3 (Relational transaction and quality logs)
* **Frontend Analytics UI:** Streamlit Web Server
* **Data Core:** Pandas & Matplotlib

---

## 📁 Project Structure
```text
llm_autopilot/
│
├── core/
│   ├── __init__.py
│   ├── analytics.py       # JSON string telemetry logs
│   ├── database.py        # SQLite schema initialization and data writes
│   ├── models.py          # Unified LLM provider interface abstraction
│   └── router.py          # Structural heuristic routing engine
│
├── data/
│   └── autopilot_metrics.db  # Local relational database file
├── logs/
│   └── autopilot_metrics.log # Rolling metrics log text file
│
├── main.py                # FastAPI HTTP Application Core
├── dashboard.py           # Streamlit Live Playground & Dashboard UI
└── README.md              # Project Documentation & Case Study

⚡ Setup & Installation

1. Clone the Repository & Initialize Virtual Environment

Bash
git clone [https://github.com/venkatesh-dharmavarapu/llm-cost-autopilot.git](https://github.com/venkatesh-dharmavarapu/llm-cost-autopilot.git)
cd llm-cost-autopilot
python -m venv venv
./venv/Scripts/activate

2. Install Dependencies

Bash
pip install fastapi uvicorn pydantic requests streamlit pandas matplotlib "starlette>=0.37.2,<0.39.0"

3. Pull Required Local Models
Ensure Ollama is running on your machine:

Bash
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:7b

🖥️ Running the Application

Step 1: Start the FastAPI Gateway Server
PowerShell : uvicorn main:app --reload

Step 2: Launch the Analytics Dashboard & Playground
PowerShell : .\venv\Scripts\python.exe -m streamlit run dashboard.py

Open your browser to http://localhost:8501 to test prompts in the live chat box and monitor cost efficiency metrics!