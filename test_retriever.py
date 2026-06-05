import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.retrieve.retriever import HybridRetriever

retriever = HybridRetriever()

print("--- Query: What is a mutual fund? ---")
res = retriever.retrieve("What is a mutual fund?")
print(res)
print("Scores:", retriever.bm25.get_scores("What is a mutual fund?".lower().split()))

print("\n--- Query: What is Debt Taxation? ---")
res2 = retriever.retrieve("What is Debt Taxation?")
print(res2)
print("Scores:", retriever.bm25.get_scores("What is Debt Taxation?".lower().split()))

