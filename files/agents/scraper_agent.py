from patchright.sync_api import sync_playwright
import logging
import time

log = logging.getLogger(__name__)

class ScraperAgent:
    """
    Stealth Scraper Agent using Patchright (Playwright fork).
    Bypasses Cloudflare/Akamai HTTP2 fingerprinting by patching the Chromium binary at the C++ level.
    """
    def __init__(self, timeout=15000):
        self.timeout = timeout
        
    def fetch_html(self, url: str) -> str:
        """
        Fetch fully rendered HTML for the given URL using Patchright.
        """
        html = ""
        log.info(f"ScraperAgent: Fetching {url}")
        
        try:
            with sync_playwright() as p:
                # Use standard headless chromium; patchright has patched it internally
                browser = p.chromium.launch(headless=True)
                
                # Create a stealthy context
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    java_script_enabled=True,
                    bypass_csp=True,
                    ignore_https_errors=True
                )
                
                page = context.new_page()
                
                # Navigate and wait for network to go idle
                page.goto(url, wait_until='networkidle', timeout=self.timeout)
                
                # Additional wait to ensure React/Angular finishes hydration
                page.wait_for_timeout(3000)
                
                html = page.content()
                browser.close()
                
        except Exception as e:
            log.error(f"ScraperAgent: Error fetching {url}: {e}")
            
        return html

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ScraperAgent()
    url = "https://www.frigidaire.com/search?query=PDSH4816AF"
    html = agent.fetch_html(url)
    print(f"Fetched {len(html)} bytes")
    if "PDSH4816AF".lower() in html.lower():
        print("Successfully found MPN in rendered HTML!")
    else:
        print("MPN not found in rendered HTML.")
