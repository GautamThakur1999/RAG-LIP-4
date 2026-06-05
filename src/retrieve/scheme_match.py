import re

# Comprehensive list of 17 ICICI Mutual Fund schemes and their common aliases
SCHEME_ALIASES = {
    "retirement_pure_equity": ["retirement pure", "pure equity"],
    "pharma": ["pharma", "healthcare", "diagnostics", "p.h.d"],
    "bharat22": ["bharat 22", "bharat22", "bharat-22"],
    "infrastructure": ["infrastructure", "infra fund"],
    "retirement_hybrid": ["retirement hybrid", "hybrid aggressive", "hybrid plan"],
    "select_large_cap": ["select large cap", "select largecap", "focused equity"],
    "india_equity": ["india equity"],
    "top100": ["top 100", "top100", "large & mid cap", "large and mid cap"],
    "diversified_equity": ["diversified equity", "all cap", "omni"],
    "value": ["value fund", "value discovery", "value plan"],
    "dynamic": ["dynamic plan", "dynamic fund", "multi asset"],
    "balanced": ["balanced fund", "balanced advantage", "balanced direct"],
    "large_cap": ["large cap", "largecap", "bluechip", "blue chip"],
    "consumption": ["consumption", "bharat consumption"],
    "income_plus_arbitrage": ["income plus", "arbitrage active", "arbitrage fund"],
    "technology": ["technology", "tech fund", "tech plan"],
    "india_opportunities": ["india opportunities", "opportunities fund"]
}

def detect_scheme(query: str):
    """
    Detects which mutual fund scheme the user is asking about.
    Returns the normalized scheme_name or None if ambiguous/missing.
    """
    query_lower = query.lower()
    
    detected = []
    for scheme, aliases in SCHEME_ALIASES.items():
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
                detected.append(scheme)
                break # Only add scheme once
                
    # If exactly one scheme is detected, return it.
    # If multiple or none are detected, return None so the retriever 
    # searches across all loaded documents instead of restricting to one.
    if len(detected) == 1:
        return detected[0]
        
    return None

def test_scheme_match():
    test_cases = [
        ("What is the expense ratio of technology fund?", "technology"),
        ("Tell me about the select large cap.", "select_large_cap"),
        ("Is the pharma fund good?", "pharma"),
        ("Compare bluechip and flexicap.", None),
        ("What is the NAV?", None)
    ]
    
    passed = 0
    for query, expected in test_cases:
        res = detect_scheme(query)
        assert res == expected, f"Failed on: {query} - Expected {expected}, got {res}"
        passed += 1
        
    print(f"Scheme Match Tests passed: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    test_scheme_match()
