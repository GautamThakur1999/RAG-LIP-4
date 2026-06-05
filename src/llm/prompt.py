import os
import csv

def build_system_prompt(chunks: list) -> str:
    """
    Builds the strict facts-only system prompt using the retrieved chunks.
    """
    
    # Load available funds dynamically
    available_funds = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    sources_file = os.path.join(data_dir, "sources.csv")
    if os.path.exists(sources_file):
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['title'].strip():
                    available_funds.append(row['title'].strip())
                    
    fund_list_str = "\n".join([f"- {f}" for f in available_funds])
    
    context_blocks = []
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "")
        source_url = chunk.get("metadata", {}).get("source_url", "Unknown Source")
        doc_date = chunk.get("metadata", {}).get("doc_as_on_date", "Unknown Date")
        fetched = chunk.get("metadata", {}).get("fetched_date", "Unknown Date")
        
        # Prefer doc_as_on_date if available, else fetched_date
        date_str = doc_date if doc_date and str(doc_date) != "nan" else fetched
        
        context_blocks.append(f"[Chunk {i+1}]\nText: {text}\nSource: {source_url}\nDate: {date_str}\n")
        
    context_str = "\n".join(context_blocks)
    
    prompt = f"""You are a strict, facts-only mutual fund FAQ assistant for ICICI Prudential Mutual Fund.
You do NOT provide investment advice.

Here is the retrieved official context from ICICI Prudential/AMFI/SEBI documents:
===
{context_str}
===

Here is the complete list of mutual funds available in the system database:
{fund_list_str}

CRITICAL RULES:
1. You MUST answer the user's question using ONLY the provided context chunks.
2. If the context does not contain the answer, you MUST say exactly: "I cannot find this information in the official documents." Do not guess or hallucinate any other funds outside the provided database list.
3. If the user asks for available funds or "another fund", strictly provide options ONLY from the list of available funds above. Do NOT make up funds.
4. Structure your answer carefully. Keep factual answers concise (≤3 sentences) unless you are outputting a list. When outputting a list, you MUST place EACH item on a completely separate line starting with a bullet point (`* `). NEVER merge list items into a single inline paragraph.
5. If quoting numbers, percentages, or dates, you MUST quote them exactly as written in the context.
"""
    return prompt
