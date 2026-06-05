import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.streamlit_app import run_pipeline

def run_test(query: str):
    print(f"\n=================================")
    print(f"QUERY: {query}")
    print(f"=================================")
    
    result = run_pipeline(query)
    print(f"KIND: {result.get('kind')}")
    print(f"ANSWER:\n{result.get('answer_text')}")
    print(f"CITATION: {result.get('citation_url')}")
    print(f"=================================\n")

if __name__ == "__main__":
    run_test("What is the exit load for the Technology Fund?")
    run_test("Who manages the Bharat 22 FOF?")
    run_test("What is the exit load for the Bluechip Fund?")
