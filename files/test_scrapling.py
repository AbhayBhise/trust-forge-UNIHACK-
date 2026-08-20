from scrapling import StealthyFetcher
import time

try:
    fetcher = StealthyFetcher(headless=True)
    url = 'https://www.frigidaire.com/search?query=PDSH4816AF'
    print(f"Fetching {url}")
    page = fetcher.fetch(url)
    
    html = page.text
    print('Length:', len(html))
    print('MPN in page:', 'PDSH4816AF'.lower() in html.lower())
    if 'PDSH4816AF'.lower() in html.lower():
        import re
        m = re.search(r'PDSH4816AF', html, re.IGNORECASE)
        if m: print('Found MPN text in page!')
        
except Exception as e:
    print(f"Error: {e}")
