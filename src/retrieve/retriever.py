import json
import os
import pickle
# NOTE: This retriever is BM25-only at runtime (no dense embeddings / ChromaDB),
# so heavy deps (chromadb, sentence-transformers, torch) are intentionally NOT
# imported here. This keeps the deployed backend slim. Do not add a top-level
# `import chromadb` back — it would break the slim Railway deploy.
from rank_bm25 import BM25Okapi
from src.retrieve.scheme_match import detect_scheme

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CHUNKS_FILE = os.path.join(PROCESSED_DIR, "chunks.jsonl")
BM25_FILE = os.path.join(DATA_DIR, "bm25_index.pkl")

# We import settings locally or define here
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
TOP_K = 5
SCORE_THRESHOLD = 0.35 # Cosine distance threshold (lower is better for distance, but higher is better for similarity)
# Note: Chroma uses cosine distance by default. Distance = 1 - Cosine Similarity.
# If we want Similarity > 0.35, Distance should be < 0.65.
MAX_DISTANCE = 1.0 - SCORE_THRESHOLD

class HybridRetriever:
    def __init__(self):
        # Relying purely on BM25 sparse search due to host AVX2 CPU limitations
        try:
            with open(BM25_FILE, 'rb') as f:
                self.bm25_data = pickle.load(f)
                self.bm25 = self.bm25_data["bm25"]
            self.initialized = True
            print(f"BM25 index loaded from {BM25_FILE}.")
        except Exception as e:
            print(f"BM25 index not found or failed to load ({e}). Attempting to build from chunks...")
            self._build_index_from_chunks()

    def _build_index_from_chunks(self):
        """Build the BM25 index from data/processed/chunks.jsonl and persist it.

        If the build succeeds, self.initialized is set to True and the index is
        saved to BM25_FILE so subsequent restarts skip this step.  If anything
        goes wrong the error is logged and self.initialized is left as False so
        the app still starts (health check will report the retriever as not ready).
        """
        try:
            if not os.path.exists(CHUNKS_FILE):
                raise FileNotFoundError(f"Chunks file not found: {CHUNKS_FILE}")

            chunks = []
            with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        chunks.append(json.loads(line))

            if not chunks:
                raise ValueError("chunks.jsonl is empty — nothing to index.")

            print(f"Building BM25 index from {len(chunks)} chunks...")

            texts = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            tokenized_corpus = [doc.lower().split() for doc in texts]
            bm25 = BM25Okapi(tokenized_corpus)

            self.bm25_data = {
                "bm25": bm25,
                "ids": ids,
                "texts": texts,
                "metadatas": metadatas,
            }
            self.bm25 = bm25

            # Persist so future restarts load instantly
            with open(BM25_FILE, 'wb') as f:
                pickle.dump(self.bm25_data, f)

            print(f"BM25 index built and saved to {BM25_FILE} ({len(chunks)} chunks).")
            self.initialized = True

        except Exception as e:
            print(f"ERROR: Failed to build BM25 index from chunks: {e}")
            self.initialized = False

    def retrieve(self, query: str):
        if not self.initialized:
            return {"status": "error", "message": "Retriever not initialized.", "chunks": []}
            
        # 1. Scheme Detection
        scheme = detect_scheme(query)
            
        # 2. Sparse Search (BM25)
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Zip scores with metadatas and filter
        sparse_hits = []
        for i, score in enumerate(bm25_scores):
            meta = self.bm25_data["metadatas"][i]
            # If scheme is detected, search in that scheme + common.
            # If no scheme is detected, search ONLY in common.
            if scheme:
                if meta["scheme_name"] in [scheme, "common"]:
                    sparse_hits.append({
                        "id": self.bm25_data["ids"][i],
                        "score": score,
                        "text": self.bm25_data["texts"][i],
                        "metadata": meta
                    })
            else:
                # No scheme specified: search ALL loaded documents
                sparse_hits.append({
                    "id": self.bm25_data["ids"][i],
                    "score": score,
                    "text": self.bm25_data["texts"][i],
                    "metadata": meta
                })
                
        # Sort sparse hits
        sparse_hits = sorted(sparse_hits, key=lambda x: x["score"], reverse=True)[:TOP_K]
        
        final_chunks = []
        for hit in sparse_hits:
            if hit["score"] > 0: # Basic threshold
                final_chunks.append({
                    "text": hit["text"],
                    "metadata": hit["metadata"],
                    "rrf_score": hit["score"]
                })
            
        if not final_chunks:
            return {
                "status": "no_hit",
                "message": "I could not find information regarding this in the loaded documents.",
                "chunks": []
            }
            
        return {
            "status": "success",
            "message": "Chunks retrieved successfully.",
            "chunks": final_chunks
        }

if __name__ == "__main__":
    print("Testing Retriever module initialization (BM25-only; fails gracefully if index missing)")
    retriever = HybridRetriever()
    if retriever.initialized:
        print("Running sample query: 'What is the expense ratio for bluechip?'")
        res = retriever.retrieve("What is the expense ratio for bluechip?")
        print(f"Status: {res['status']}")
        for c in res['chunks']:
            print(f"- {c['metadata']['source_url']} (RRF: {c['rrf_score']:.3f})")
    else:
        print("Skipping queries due to initialization failure.")
