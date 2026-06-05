from src.retrieve.retriever import HybridRetriever
from src.llm.client import GroqClient
from src.llm.prompt import build_system_prompt
from src.guardrails.pii import check_pii
from src.guardrails.intent import get_intent

def generate_answer(query: str, retriever: HybridRetriever, llm_client: GroqClient) -> dict:
    """
    Orchestrates the complete Generation pipeline:
    query -> pii.check -> intent.classify -> retrieve -> generate
    """
    # 1. PII Check
    is_blocked, pii_msg = check_pii(query)
    if is_blocked:
        return {
            "answer_text": pii_msg,
            "citation_url": None,
            "last_updated": None,
            "kind": "refusal"
        }
        
    # 2. Intent Classification
    # Note: We pass None for llm_client because we are only using the keyword pre-filter currently, 
    # but we could pass llm_client for deeper stage 2 classification.
    intent_label, fallback_link = get_intent(query, llm_client=None)
    
    if intent_label == "advisory":
        return {
            "answer_text": "I am a facts-only assistant and cannot provide investment advice or recommendations. Please refer to official educational resources.",
            "citation_url": fallback_link,
            "last_updated": None,
            "kind": "refusal"
        }
    elif intent_label == "out_of_scope":
        return {
            "answer_text": "This query is out of scope. I can only answer factual questions about ICICI Prudential mutual funds.",
            "citation_url": None,
            "last_updated": None,
            "kind": "refusal"
        }
        
    # 3. Retrieval
    retrieval_res = retriever.retrieve(query)
    
    if retrieval_res["status"] == "error":
        return {
            "answer_text": "System error: " + retrieval_res["message"],
            "citation_url": None,
            "last_updated": None,
            "kind": "refusal"
        }
        
    if retrieval_res["status"] == "need_clarification":
        return {
            "answer_text": retrieval_res["message"],
            "citation_url": None,
            "last_updated": None,
            "kind": "refusal"
        }
        
    if retrieval_res["status"] == "no_hit":
        return {
            "answer_text": retrieval_res["message"],
            "citation_url": None,
            "last_updated": None,
            "kind": "refusal"
        }
        
    chunks = retrieval_res["chunks"]
    
    # 4. Generate Answer
    system_prompt = build_system_prompt(chunks)
    answer = llm_client.complete(system_prompt, query, temperature=0.0)
    
    # 5. Extract the single primary citation
    primary_chunk = chunks[0]
    citation_url = primary_chunk.get("metadata", {}).get("source_url", "Unknown Source")
    doc_date = primary_chunk.get("metadata", {}).get("doc_as_on_date")
    fetched = primary_chunk.get("metadata", {}).get("fetched_date")
    last_updated = doc_date if doc_date and str(doc_date) != "nan" else fetched

    return {
        "answer_text": answer,
        "citation_url": citation_url,
        "last_updated": last_updated,
        "kind": "factual"
    }

if __name__ == "__main__":
    print("Testing Generation pipeline...")
    retriever = HybridRetriever()
    client = GroqClient()
    
    # Test queries covering all paths
    test_queries = [
        "What is the expense ratio of the bluechip fund?",  # Factual (requires retriever)
        "Should I buy the flexicap fund right now?",        # Advisory (intent)
        "Here is my PAN ABCDE1234F, what is the exit load?" # PII blocked
    ]
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        if retriever.initialized and client.client:
            res = generate_answer(q, retriever, client)
            print(f"[{res['kind'].upper()}] {res['answer_text']}")
            if res['citation_url']:
                print(f"Citation: {res['citation_url']}")
        else:
            print("Skipping LLM/Retriever execution (Not fully initialized). Testing logic paths only.")
            # We can still test PII and intent even without the LLM/Retriever
            res = generate_answer(q, HybridRetriever(), GroqClient())
            print(f"Fallback Path output: {res['kind']} - {res['answer_text']}")
