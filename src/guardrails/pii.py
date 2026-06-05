import re

def check_pii(query: str):
    """
    Checks the query for PII (PAN, Aadhaar, phone, email, etc.)
    Returns (True, refusal_message) if blocked, else (False, "")
    """
    # Regex patterns
    # PAN: 5 letters, 4 digits, 1 letter
    pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', re.IGNORECASE)
    
    # Aadhaar: 12 digits, optional spaces
    aadhaar_pattern = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
    
    # Phone: Indian formats
    phone_pattern = re.compile(r'(\+91[\-\s]?)?[6-9]\d{9}\b')
    
    # Email
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
    
    # Keywords
    blocked_keywords = ["account number", "folio", "otp", "password"]
    query_lower = query.lower()

    if pan_pattern.search(query):
        return True, "Request blocked. Please do not share sensitive information like your PAN."
        
    if aadhaar_pattern.search(query):
        return True, "Request blocked. Please do not share sensitive information like your Aadhaar number."
        
    if phone_pattern.search(query):
        return True, "Request blocked. Please do not share sensitive information like your phone number."
        
    if email_pattern.search(query):
        return True, "Request blocked. Please do not share sensitive information like your email address."

    for kw in blocked_keywords:
        if kw in query_lower:
            return True, f"Request blocked. Please do not share sensitive information like your {kw}."

    return False, ""

def test_pii():
    test_cases = [
        ("My PAN is ABCDE1234F, tell me the balance.", True),
        ("What is the minimum SIP?", False),
        ("My Aadhaar is 1234 5678 9012.", True),
        ("Is the expense ratio 1.5?", False),
        ("Launched in 2008, what is its performance?", False),
        ("Call me at 9876543210", True),
        ("Email me at test@example.com", True),
        ("Here is my folio 12345", True),
        ("What is the exit load?", False)
    ]
    
    passed = 0
    for text, expected_block in test_cases:
        blocked, msg = check_pii(text)
        assert blocked == expected_block, f"Failed on: {text} - Expected blocked={expected_block}, got {blocked}"
        passed += 1
    
    print(f"PII Tests passed: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    test_pii()
