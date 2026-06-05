import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.retrieve.retriever import HybridRetriever

retriever = HybridRetriever()

print("--- Query 1 ---")
res = retriever.retrieve("What is the exit load for the Technology Fund?")
print(f"Status: {res['status']}")
if res['chunks']:
    print(res['chunks'][0]['text'][:300])

print("--- Query 2 ---")
res = retriever.retrieve("Who manages the Bharat 22 FOF?")
print(f"Status: {res['status']}")
if res['chunks']:
    print(res['chunks'][0]['text'][:300])
