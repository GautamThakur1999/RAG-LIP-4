import os
import pickle
import chromadb
from src.retrieve.scheme_match import detect_scheme

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
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
        except Exception as e:
            print(f"Retriever initialization failed (Index might not exist yet): {e}")
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
    print("Testing Retriever module initialization (will fail gracefully if PyTorch/Chroma not ready)")
    retriever = HybridRetriever()
    if retriever.initialized:
        print("Running sample query: 'What is the expense ratio for bluechip?'")
        res = retriever.retrieve("What is the expense ratio for bluechip?")
        print(f"Status: {res['status']}")
        for c in res['chunks']:
            print(f"- {c['metadata']['source_url']} (RRF: {c['rrf_score']:.3f})")
    else:
        print("Skipping queries due to initialization failure.")
