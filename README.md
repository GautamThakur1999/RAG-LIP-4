# 📈 ICICI Prudential AI Mutual Fund Assistant (RAG Pipeline)

A robust, compliance-first AI assistant designed exclusively to provide factual information about ICICI Prudential mutual fund schemes. Built using a modern Retrieval-Augmented Generation (RAG) architecture with strict guardrails against PII leakage and unauthorized financial advisory.

## 🌟 Key Features
- **Strictly Factual & Verifiable**: All AI outputs are grounded in official scheme factsheets. Every response is guaranteed to be ≤3 sentences and includes exactly one source citation with a "Last updated" timestamp.
- **Hybrid Retrieval System**: Combines dense semantic search (ChromaDB + SentenceTransformers) with sparse lexical search (BM25) to ensure hyper-accurate data retrieval across highly technical financial texts.
- **Ironclad Guardrails**: Natively detects and blocks Personally Identifiable Information (PAN, Aadhaar, Phone Numbers) and immediately intercepts advisory questions ("Should I invest?", "Which is better?"), cleanly redirecting users to official SEBI resources.
- **Zero Hallucination Guarantee**: If the database lacks the exact fact requested, the system politely declines to answer rather than guessing.
- **Daily Background Automation**: Natively hooked into Windows Task Scheduler to run the entire extraction, chunking, indexing, and evaluation pipeline continuously at 10:00 AM IST.

## 🏗️ Architecture Stack
- **Frontend**: Streamlit
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **Vector Database**: ChromaDB (Local)
- **Sparse Indexing**: `rank_bm25`
- **Embeddings**: `all-MiniLM-L6-v2`
- **Evaluation**: Custom Pytest-style test harnesses

## 🚀 Getting Started

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/GautamThakur1999/RAG-LIP-4.git
cd "RAG LIP 4"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory (use `.env.example` as a template):
```ini
GROQ_API_KEY=your_api_key_here
SCORE_THRESHOLD=1.2
```

### 3. Build the Database (First Run)
Before running the UI, you must ingest the data and build the Vector/BM25 indices:
```bash
python src/ingest/fetch.py
python src/ingest/parse.py
python src/ingest/chunk.py
python src/ingest/build_index.py
```

### 4. Run the App
Launch the Streamlit interface:
```bash
streamlit run app/streamlit_app.py
```

## ⏱️ Daily Automation
This project ships with a pre-configured background task that runs the entire ingestion and evaluation pipeline daily at **10:00 AM IST** to ensure the database is always fresh.
To register the task on Windows, simply double-click `run_daily.bat` or manually trigger the Task Scheduler registration:
```bash
schtasks /create /tn "RAG_MutualFund_Daily_Job" /tr "c:\absolute\path\to\run_daily.bat" /sc DAILY /st 10:00 /f
```
You can view the output of the automated runs in `eval/daily_job_output.log`.

## 🛡️ Evaluation Suite
The system includes a rigorous evaluation suite testing 15 edge cases (10 factual checks, 5 PII/Advisory checks). To run the suite manually:
```bash
python eval/run_eval.py
```
Passing Q&A factual pairs are dynamically exported to `deliverables/sample_qa.md`.

---
*Built as a secure, compliance-first prototype for factual mutual fund querying.*
