import os
import json
import pickle
import time
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from rank_bm25 import BM25Okapi

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CHUNKS_FILE = os.path.join(PROCESSED_DIR, "chunks.jsonl")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
BM25_FILE = os.path.join(DATA_DIR, "bm25_index.pkl")
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")

# Model configuration from config/env
# We use bge-small-en-v1.5
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

def build_index():
    if not os.path.exists(CHUNKS_FILE):
        print(f"Error: {CHUNKS_FILE} not found. Run chunk.py first.")
        return

    # Load chunks
    chunks = []
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    if not chunks:
        print("No chunks to index.")
        return

    print(f"Loaded {len(chunks)} chunks.")
    
    # 3. Skip Dense Embeddings due to AVX2 CPU limitations on Windows
    # We will rely entirely on BM25 sparse search for RAG.
    # ids = [f"chunk_{i}" for i in range(len(chunks))]

    # 4. Build BM25 Index
    print("Building BM25 Index...")
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    tokenized_corpus = [doc.lower().split() for doc in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    bm25_data = {
        "bm25": bm25,
        "ids": ids,
        "texts": texts,
        "metadatas": metadatas
    }
    
    with open(BM25_FILE, 'wb') as f:
        pickle.dump(bm25_data, f)

    # 5. Write Manifest
    manifest = {
        "embed_model": "bm25-only",
        "embed_dim": 0,
        "corpus_build_date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "chunk_count": len(chunks)
    }
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print("--------------------")
    print("Indexing Complete!")
    print(f"Chunks Indexed: {len(chunks)}")
    print(f"Embed Model: BM25 Only (dim: 0)")
    print(f"Data Dir: {PROCESSED_DIR}")
    print(f"ChromaDB Path: {CHROMA_DIR}")
    print(f"BM25 Path: {BM25_FILE}")

if __name__ == "__main__":
    build_index()
