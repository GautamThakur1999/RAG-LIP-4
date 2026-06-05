import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.retrieve.retriever import HybridRetriever
from src.llm.client import GroqClient
from src.llm.answer import generate_answer

def run_evaluation():
    testset_path = os.path.join(os.path.dirname(__file__), 'testset.json')
    if not os.path.exists(testset_path):
        print("Error: testset.json not found.")
        return

    with open(testset_path, 'r', encoding='utf-8') as f:
        testset = json.load(f)

    print("Initializing LLM client and Retriever...")
    retriever = HybridRetriever()
    client = GroqClient()
    
    if not retriever.initialized or not client.client:
        print("Error: Retriever or LLM client failed to initialize.")
        return

    total = len(testset)
    passed = 0
    passed_factual_cases = []

    print(f"Running evaluation on {total} cases...\n")

    for i, case in enumerate(testset):
        query = case['query']
        expected_type = case['type']
        expected_fact = case['expected_fact'].lower()
        expected_url = case['expected_url']

        print(f"[{i+1}/{total}] Query: {query}")
        
        result = generate_answer(query, retriever, client)
        
        # Check assertions
        case_passed = True
        failure_reasons = []

        if result['kind'] != expected_type:
            case_passed = False
            failure_reasons.append(f"Expected kind '{expected_type}', got '{result['kind']}'")
        
        if expected_type == "factual":
            # 1. Must contain the expected fact
            if expected_fact and expected_fact not in result['answer_text'].lower():
                # Allow partial match or just log it
                case_passed = False
                failure_reasons.append(f"Expected fact '{expected_fact}' not found in answer.")
            
            # 2. Exactly one valid URL matching expected
            if result['citation_url'] != expected_url:
                case_passed = False
                failure_reasons.append(f"Expected URL '{expected_url}', got '{result['citation_url']}'")
            
            # 3. Concise: rough check of sentences using period split
            sentences = [s for s in result['answer_text'].split('.') if len(s.strip()) > 5]
            # If it's a list, it might have many lines, so we ignore sentence count if there's a list formatting (* )
            if "* " not in result['answer_text'] and len(sentences) > 4: # Allowing a bit of leeway for titles
                case_passed = False
                failure_reasons.append(f"Answer is too long: {len(sentences)} sentences.")
                
            if case_passed:
                passed_factual_cases.append({
                    "query": query,
                    "answer": result['answer_text'],
                    "citation": result['citation_url'],
                    "last_updated": result.get('last_updated', 'Unknown')
                })
                
        elif expected_type == "refusal":
            # For advisory, check edu link
            if "Should" in query or "better" in query or "good time" in query:
                if not result['citation_url'] or "investor.sebi.gov.in" not in result['citation_url']:
                    case_passed = False
                    failure_reasons.append("Advisory refusal missing SEBI link.")
            
            # PII check
            if "PAN" in query or "phone" in query:
                if "ABCDE1234F" in result['answer_text'] or "9876543210" in result['answer_text']:
                    case_passed = False
                    failure_reasons.append("PII leaked in response.")

        if case_passed:
            print("[PASS]")
            passed += 1
        else:
            print("[FAIL]")
            for reason in failure_reasons:
                print(f"   -> {reason}")
            print(f"   -> LLM Answer: {result['answer_text']}")

    print("\n" + "="*40)
    print(f"EVALUATION COMPLETE: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    print("="*40 + "\n")

    # Generate Deliverable
    if passed_factual_cases:
        deliverables_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deliverables')
        os.makedirs(deliverables_dir, exist_ok=True)
        qa_path = os.path.join(deliverables_dir, 'sample_qa.md')
        
        with open(qa_path, 'w', encoding='utf-8') as f:
            f.write("# Sample Q&A\n\n")
            f.write("Generated from automated factual test cases.\n\n")
            for item in passed_factual_cases:
                f.write(f"**Q: {item['query']}**\n\n")
                f.write(f"**A:** {item['answer']}\n\n")
                f.write(f"📖 *Source: [{item['citation']}]({item['citation']})*\n")
                f.write(f"🕒 *Last updated: {item['last_updated']}*\n")
                f.write("---\n\n")
                
        print(f"Generated {qa_path} with {len(passed_factual_cases)} passing factual cases.")

if __name__ == "__main__":
    run_evaluation()
