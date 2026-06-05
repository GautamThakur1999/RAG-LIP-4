from bs4 import BeautifulSoup

with open("test_groww.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Fund Details
details = soup.find(class_="fundDetails_fundDetailsContainer__SLn0o")
if details:
    print("FUND DETAILS:")
    print(details.get_text(separator='\n', strip=True))

# Scheme Information
for section in soup.find_all("section"):
    print("--- SECTION ---")
    print(section.get_text(separator='\n', strip=True)[:300])

