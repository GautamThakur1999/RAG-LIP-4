import os
from pathlib import Path

def create_file(path_str, content=""):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

dirs = [
    "data/raw",
    "data/processed",
    "src/ingest",
    "src/guardrails",
    "src/retrieve",
    "src/generate",
    "src/llm",
    "app",
    "eval",
    "deliverables"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

modules = [
    "src/ingest/fetch.py",
    "src/ingest/parse.py",
    "src/ingest/chunk.py",
    "src/ingest/build_index.py",
    "src/guardrails/pii.py",
    "src/guardrails/intent.py",
    "src/retrieve/retriever.py",
    "src/retrieve/scheme_match.py",
    "src/generate/prompt.py",
    "src/generate/answer.py",
    "src/llm/client.py",
    "app/streamlit_app.py",
    "eval/run_eval.py"
]

for mod in modules:
    content = f'''"""
Module: {mod}
"""

if __name__ == "__main__":
    print("Module: {mod}")
'''
    create_file(mod, content)

req_content = """requests
beautifulsoup4
pdfplumber
pymupdf
langchain-text-splitters
sentence-transformers
chromadb
rank-bm25
pydantic-settings
python-dotenv
streamlit
pytest
tqdm
"""
create_file("requirements.txt", req_content)

env_example_content = """LLM_API_KEY=your_api_key_here
LLM_MODEL=openai/gpt-4o-mini
EMBED_MODEL=BAAI/bge-small-en-v1.5
TOP_K=5
SCORE_THRESHOLD=0.35
MAX_SENTENCES=3
"""
create_file(".env.example", env_example_content)

gitignore_content = """.env
data/raw/
__pycache__/
*.sqlite3
chroma_db/
.venv/
"""
create_file(".gitignore", gitignore_content)

config_content = '''from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 5
    score_threshold: float = 0.35
    max_sentences: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

if __name__ == "__main__":
    print("Loaded settings:")
    print(settings.model_dump())
'''
create_file("config.py", config_content)

rules_content = """- This is a facts-only mutual fund FAQ RAG. No investment advice, ever.
- Answers come ONLY from retrieved corpus chunks. If not retrieved, refuse.
- Every factual answer: <=3 sentences, exactly ONE source URL, footer
  "Last updated from sources: <date>".
- Never compute/compare returns. Redirect performance questions to the factsheet.
- Block PII (PAN, Aadhaar, account/folio, OTP, email, phone); never store it.
- Corpus = ICICI Prudential official site + AMFI/SEBI only. Plan = Direct-Growth.
- Prefer small, testable functions. Add a runnable __main__ smoke test per module.
"""
create_file("rules.md", rules_content)

create_file("README.md", "# Mutual Fund FAQ Assistant\n")
create_file("data/sources.csv", "url,source_type,scheme,title,fetched_date\n")
create_file("eval/testset.json", "{}")
create_file("deliverables/sample_qa.md", "")
create_file("deliverables/disclaimer.md", "")

print("Scaffolding complete.")
