import csv
import os
import time
import hashlib
import urllib.robotparser
from urllib.parse import urlparse
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
SOURCES_CSV = os.path.join(DATA_DIR, "sources.csv")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MutualFundBot/1.0"

def get_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def can_fetch(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        # If we can't fetch robots.txt, assume allowed
        return True

def fetch_all():
    os.makedirs(RAW_DIR, exist_ok=True)
    
    if not os.path.exists(SOURCES_CSV):
        print(f"Error: {SOURCES_CSV} not found.")
        return

    fetched_count = 0
    cached_count = 0
    failed_count = 0

    with open(SOURCES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    updated_rows = []

    for row in rows:
        url = row['url'].strip()
        if not url:
            updated_rows.append(row)
            continue
            
        file_hash = get_hash(url)
        # Check if url ends in pdf or source_type indicates pdf
        is_pdf = url.lower().endswith(".pdf") or row['source_type'] in ['factsheet', 'sid', 'kim', 'statement_guide']
        ext = ".pdf" if is_pdf else ".html"
        save_path = os.path.join(RAW_DIR, f"{file_hash}{ext}")

        if os.path.exists(save_path):
            print(f"Cached: {url}")
            cached_count += 1
            updated_rows.append(row)
            continue

        if not can_fetch(url):
            print(f"Blocked by robots.txt: {url}")
            failed_count += 1
            updated_rows.append(row)
            continue

        try:
            print(f"Fetching: {url}")
            headers = {"User-Agent": USER_AGENT}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as out_f:
                    out_f.write(response.content)
                row['fetched_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
                fetched_count += 1
            else:
                print(f"Failed ({response.status_code}): {url}")
                failed_count += 1
                
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            failed_count += 1

        updated_rows.append(row)
        time.sleep(1) # Small delay to be polite

    # Write back the updated fetched_date if anything was fetched
    if fetched_count > 0:
        with open(SOURCES_CSV, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

    print("-" * 20)
    print(f"Total processed: {len(rows)}")
    print(f"Newly fetched: {fetched_count}")
    print(f"Used cache: {cached_count}")
    print(f"Failed: {failed_count}")

if __name__ == "__main__":
    fetch_all()
