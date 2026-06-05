import re

ADVISORY_KEYWORDS = [
    "should i", "better", "buy", "sell", "recommend", 
    "worth it", "which fund", "good investment", "compare",
    "switch", "portfolio"
]

FALLBACK_LINK = "https://investor.sebi.gov.in/mutual-funds.html"

def check_intent_keyword(query: str):
    """
    Stage 1: Fast keyword-based intent routing.
    Returns (label, fallback_link)
    """
    query_lower = query.lower()
    for kw in ADVISORY_KEYWORDS:
        if re.search(r'\b' + kw + r'\b', query_lower):
            return "advisory", FALLBACK_LINK
    
    # If no advisory keywords found, default to factual
    # (Stage 2 LLM classifier would go here)
    return "factual", ""

def classify_intent_llm(query: str, llm_client):
    """
    Stage 2: LLM based classification.
    Expects llm_client to have a complete() method.
    """
    # This is a stub for the LLM call that will be wired up in Phase 5
    system_prompt = """
    Classify the following mutual fund user query into exactly one of these three categories:
    1. 'factual' - Asking for facts, fees, numbers, dates, or concepts.
    2. 'advisory' - Asking for recommendations, whether to buy/sell, or comparing funds for investment.
    3. 'out_of_scope' - Completely unrelated to mutual funds or ICICI Prudential.
    Respond with ONLY the category name.
    """
    
    try:
        response = llm_client.complete(system_prompt, query, temperature=0.0)
        label = response.strip().lower()
        if label not in ['factual', 'advisory', 'out_of_scope']:
            return "factual", "" # Default fallback
            
        if label == "advisory":
            return label, FALLBACK_LINK
        return label, ""
    except Exception as e:
        print(f"LLM Classification error: {e}")
        return "factual", ""

def get_intent(query: str, llm_client=None):
    """Orchestrates Stage 1 and Stage 2 intent classification"""
    label, link = check_intent_keyword(query)
    if label == "advisory":
        return label, link
        
    if llm_client:
        return classify_intent_llm(query, llm_client)
        
    return label, link

def test_intent():
    test_cases = [
        ("Should I buy ICICI Bluechip?", "advisory"),
        ("What is the exit load?", "factual"),
        ("Which fund is better, flexicap or bluechip?", "advisory"),
        ("Tell me the expense ratio.", "factual"),
        ("Can you recommend a good tax saver?", "advisory")
    ]
    
    passed = 0
    for query, expected_label in test_cases:
        label, link = get_intent(query)
        assert label == expected_label, f"Failed on: {query} - Expected {expected_label}, got {label}"
        passed += 1
        
    print(f"Intent Tests passed: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    test_intent()
