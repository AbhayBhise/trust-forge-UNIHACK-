from playwright.sync_api import sync_playwright
import time

def test_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        url = 'https://www.frigidaire.com/search?query=PDSH4816AF'
        print(f"Fetching {url}")
        page.goto(url, wait_until='networkidle')
        # wait a bit for any lazy loaded specs
        page.wait_for_timeout(3000)
        
        html = page.content()
        print('Length:', len(html))
        print('MPN in page:', 'PDSH4816AF'.lower() in html.lower())
        browser.close()

if __name__ == '__main__':
    test_playwright()
