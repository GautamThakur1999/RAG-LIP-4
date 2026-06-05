import os
import re
import json
import csv
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SOURCES_CSV = os.path.join(DATA_DIR, "sources.csv")
CHUNKS_FILE = os.path.join(PROCESSED_DIR, "chunks.jsonl")

# We use character splitter simulating token splitting since we want about ~400 tokens
# Roughly 4 chars per token -> ~1600 chars. Overlap ~15% -> ~240 chars.
CHUNK_SIZE = 1600
CHUNK_OVERLAP = 240

def extract_identity_block(text, scheme_name):
    # Try to find fund manager, category, inception in the text
    identity_lines = []
    
    fm_match = re.search(r'(?i)(?:fund manager[s]?|managed by)[:\s]+([^.\n]{3,40})', text)
    if fm_match:
        identity_lines.append(f"Fund manager: {fm_match.group(1).strip()}")
        
    cat_match = re.search(r'(?i)(?:category|scheme category)[:\s]+([^.\n]{3,40})', text)
    if cat_match:
        identity_lines.append(f"Category: {cat_match.group(1).strip()}")
        
    inc_match = re.search(r'(?i)(?:inception date|date of inception|launch date)[:\s]+([^.\n]{5,20})', text)
    if inc_match:
        identity_lines.append(f"Inception Date: {inc_match.group(1).strip()}")
        
    if identity_lines:
        return f"Scheme: {scheme_name}\n" + "\n".join(identity_lines)
    return None

def chunk_text(text, metadata):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n--- EXTRACTED TABLES ---\n", "\n\n", "\n", ".", " ", ""]
    )
    
    # Split the main text
    raw_chunks = splitter.split_text(text)
    
    final_chunks = []
    
    # 1. Identity Rule
    identity_block = extract_identity_block(text, metadata['scheme_name'])
    if identity_block:
        final_chunks.append({
            "text": identity_block,
            "metadata": metadata.copy()
        })
    
    # 2. Process all chunks
    for chunk in raw_chunks:
        chunk_text = chunk.strip()
        if not chunk_text:
            continue
            
        # 3. Table Rule (prepend scheme name)
        if ":" in chunk_text and "\n" not in chunk_text and len(chunk_text) < 200:
            # It's likely a table row
            chunk_text = f"Scheme: {metadata['scheme_name']}\n{chunk_text}"
            
        final_chunks.append({
            "text": chunk_text,
            "metadata": metadata.copy()
        })
        
    return final_chunks

def chunk_all():
    if not os.path.exists(SOURCES_CSV):
        print(f"Error: {SOURCES_CSV} not found.")
        return

    # Load source metadata
    sources = {}
    with open(SOURCES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['url'].strip()
            if url:
                file_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
                sources[file_hash] = row

    all_chunks = []
    
    if not os.path.exists(PROCESSED_DIR):
        print(f"Error: {PROCESSED_DIR} not found. Run parse.py first.")
        return

    for filename in os.listdir(PROCESSED_DIR):
        if not filename.endswith(".txt"):
            continue
            
        file_hash = filename.replace(".txt", "")
        source_meta = sources.get(file_hash)
        
        if not source_meta:
            continue

        filepath = os.path.join(PROCESSED_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse out our custom header
        parts = content.split("-" * 40 + "\n", 1)
        if len(parts) == 2:
            header, text = parts
            
            # Extract As On Date
            as_on_date = ""
            for line in header.split('\n'):
                if line.startswith("As On Date:"):
                    as_on_date = line.replace("As On Date:", "").strip()
        else:
            text = content
            as_on_date = ""

        metadata = {
            "source_url": source_meta['url'],
            "source_type": source_meta['source_type'],
            "scheme_name": source_meta['scheme'],
            "plan_type": "Direct-Growth",
            "fetched_date": source_meta.get('fetched_date', ''),
            "doc_as_on_date": as_on_date
        }

        chunks = chunk_text(text, metadata)
        all_chunks.extend(chunks)

    # Write chunks.jsonl
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        for c in all_chunks:
            f.write(json.dumps(c) + "\n")

    print(f"Generated {len(all_chunks)} chunks to {CHUNKS_FILE}")

if __name__ == "__main__":
    chunk_all()
