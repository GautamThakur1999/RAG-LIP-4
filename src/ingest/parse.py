import os
import re
import csv
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pdfplumber

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SOURCES_CSV = os.path.join(DATA_DIR, "sources.csv")

def extract_date(text):
    # Looking for something like "Data as on 31 Jan 2024" or "As on 31-01-2024"
    match = re.search(r'(?i)(?:data\s+as\s+on|as\s+on|as\s+of)\s*[:\-]?\s*(\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})', text)
    if match:
        return match.group(1).strip()
    return ""

def parse_html(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    # Strip irrelevant parts
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()
        
    text = soup.get_text(separator='\n')
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    return text, extract_date(text)

def parse_pdf(filepath):
    text_content = []
    
    # 1. Extract text with PyMuPDF (fast, good layout)
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text_content.append(page.get_text())
        doc.close()
    except Exception as e:
        print(f"Error reading PDF text {filepath}: {e}")

    full_text = "\n".join(text_content)
    as_on_date = extract_date(full_text)

    # 2. Extract tables with pdfplumber
    table_blocks = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    # Convert table to structured text block
                    # Assume first row is header if it exists
                    valid_rows = [row for row in table if row and any(cell for cell in row if cell and str(cell).strip())]
                    if not valid_rows:
                        continue
                        
                    header = valid_rows[0]
                    for row in valid_rows[1:]:
                        if len(row) == len(header):
                            # Label: Value format
                            for k, v in zip(header, row):
                                if k and v:
                                    # Clean up newlines in cells
                                    k_clean = str(k).replace('\n', ' ').strip()
                                    v_clean = str(v).replace('\n', ' ').strip()
                                    if k_clean and v_clean:
                                        table_blocks.append(f"{k_clean}: {v_clean}")
    except Exception as e:
        print(f"Error reading PDF tables {filepath}: {e}")

    # Combine text and table blocks
    final_text = full_text + "\n\n--- EXTRACTED TABLES ---\n" + "\n".join(table_blocks)
    
    # Clean up whitespace
    lines = [line.strip() for line in final_text.split('\n') if line.strip()]
    final_text = '\n'.join(lines)
    
    return final_text, as_on_date

def parse_all():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    if not os.path.exists(SOURCES_CSV):
        print(f"Error: {SOURCES_CSV} not found.")
        return

    with open(SOURCES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    processed_count = 0

    for row in rows:
        url = row['url'].strip()
        if not url:
            continue
            
        import hashlib
        file_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        is_pdf = url.lower().endswith(".pdf") or row['source_type'] in ['factsheet', 'sid', 'kim', 'statement_guide']
        ext = ".pdf" if is_pdf else ".html"
        raw_path = os.path.join(RAW_DIR, f"{file_hash}{ext}")
        processed_path = os.path.join(PROCESSED_DIR, f"{file_hash}.txt")

        if not os.path.exists(raw_path):
            continue

        print(f"Parsing: {raw_path}")
        try:
            if is_pdf:
                text, date_val = parse_pdf(raw_path)
            else:
                text, date_val = parse_html(raw_path)
                
            # Write processed text
            with open(processed_path, 'w', encoding='utf-8') as out_f:
                out_f.write(f"URL: {url}\n")
                out_f.write(f"Type: {row['source_type']}\n")
                out_f.write(f"Scheme: {row['scheme']}\n")
                out_f.write(f"Fetched: {row.get('fetched_date', '')}\n")
                out_f.write(f"As On Date: {date_val}\n")
                out_f.write("-" * 40 + "\n")
                out_f.write(text)
                
            processed_count += 1
        except Exception as e:
            print(f"Error parsing {raw_path}: {e}")

    print("-" * 20)
    print(f"Parsed and saved {processed_count} files to data/processed/")

if __name__ == "__main__":
    parse_all()
