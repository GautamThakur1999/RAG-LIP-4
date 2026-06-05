import os
import sys
import csv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieve.retriever import HybridRetriever
from src.llm.client import GroqClient
from src.llm.answer import generate_answer

# Global singleton instances for retriever and LLM client
retriever = None
llm_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan event handler (replaces deprecated on_event)."""
    global retriever, llm_client
    print("Initializing Retriever and LLM Client...")
    retriever = HybridRetriever()
    llm_client = GroqClient()
    yield
    # Shutdown: nothing to clean up

app = FastAPI(
    title="ICICI Prudential Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
frontend_url = os.environ.get("FRONTEND_URL", "")
allowed_origins = ["http://localhost:3000"]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """Lightweight health endpoint for Railway healthchecks and uptime probes.
    Reports whether the retriever index and LLM client initialized."""
    return {
        "status": "ok",
        "service": "ICICI Prudential Assistant API",
        "retriever_ready": bool(retriever and getattr(retriever, "initialized", False)),
        "llm_ready": bool(llm_client and getattr(llm_client, "client", None)),
    }


class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    citation: str | None
    last_updated: str | None
    kind: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    global retriever, llm_client
    if not retriever or not retriever.initialized or not llm_client or not llm_client.client:
        raise HTTPException(status_code=503, detail="AI Services are not fully initialized yet.")
        
    try:
        res = generate_answer(request.query, retriever, llm_client)
        return ChatResponse(
            answer=res.get("answer_text", ""),
            citation=res.get("citation_url"),
            last_updated=res.get("last_updated"),
            kind=res.get("kind", "refusal")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sources")
async def sources_endpoint():
    sources_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sources.csv")
    if not os.path.exists(sources_file):
        return []
        
    sources = []
    try:
        with open(sources_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('url'):
                    sources.append(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading sources: {str(e)}")
        
    return sources

if __name__ == "__main__":
    # Local dev entrypoint. In production Railway uses the Procfile:
    #   web: uvicorn app.api:app --host 0.0.0.0 --port $PORT
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port)
