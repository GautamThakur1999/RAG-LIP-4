import sys
import os
import requests
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ingest.parse import parse_html

url = "https://groww.in/mutual-funds/icici-prudential-technology-fund-direct-growth"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers)
with open("test_groww.html", "w", encoding="utf-8") as f:
    f.write(r.text)

text, date_val = parse_html("test_groww.html")
print(f"Extracted Date: '{date_val}'")
print("-" * 20)
print(text[:1500])
