import csv
import urllib.request
import urllib.error
import ssl

def check_urls(csv_file):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['url']
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    print(f"OK ({response.status}) - {url}")
            except urllib.error.HTTPError as e:
                print(f"HTTP ERROR ({e.code}) - {url}")
            except urllib.error.URLError as e:
                print(f"URL ERROR ({e.reason}) - {url}")
            except Exception as e:
                print(f"ERROR ({str(e)}) - {url}")

if __name__ == '__main__':
    check_urls('data/sources.csv')
