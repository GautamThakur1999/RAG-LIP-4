from bs4 import BeautifulSoup
import re

with open("test_groww.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
    element.decompose()

text = soup.get_text(separator='\n', strip=True)

# Print lines containing Exit, Load, Expense
for i, line in enumerate(text.split('\n')):
    if re.search(r'(?i)exit|load|expense|manager|objective', line):
        print(f"Line {i}: {line}")
