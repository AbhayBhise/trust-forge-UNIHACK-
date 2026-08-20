import logging
import requests
import json
from ddgs import DDGS
from patchright.sync_api import sync_playwright
from html_spec_extractor import SpecBlockExtractor

log = logging.getLogger(__name__)

class AdaptiveScraperAgent:
    """
    Attempts multiple strategies to extract HTML from a URL:
    1. Standard Requests
    2. Wayback Machine (Bypass Cloudflare/Akamai HTTP2 blocks)
    3. Patchright (Stealth Headless Chrome)
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }

    def fetch(self, url: str) -> str:
        # Strategy 1: Wayback Machine for known blocked domains
        if "frigidaire.com" in url or "whirlpool.com" in url:
            log.info(f"AdaptiveScraperAgent: Domain known to block. Trying Wayback Machine for {url}")
            wb_url = f"http://archive.org/wayback/available?url={url}"
            try:
                wb_data = requests.get(wb_url, timeout=10).json()
                if wb_data.get("archived_snapshots") and "closest" in wb_data["archived_snapshots"]:
                    snapshot_url = wb_data["archived_snapshots"]["closest"]["url"]
                    log.info(f"AdaptiveScraperAgent: Found Wayback snapshot: {snapshot_url}")
                    r = requests.get(snapshot_url, headers=self.headers, timeout=15)
                    if r.status_code == 200:
                        return r.text
            except Exception as e:
                log.warning(f"Wayback Machine strategy failed: {e}")

        # Strategy 2: Standard Requests (fastest)
        try:
            log.info(f"AdaptiveScraperAgent: Trying standard requests for {url}")
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200 and len(r.text) > 5000:
                if "Please enable JavaScript" not in r.text and "Cloudflare" not in r.text and "human verification" not in r.text:
                    return r.text
        except Exception:
            pass

        # Strategy 3: Patchright Stealth
        try:
            log.info(f"AdaptiveScraperAgent: Trying Patchright for {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.headers['User-Agent'], ignore_https_errors=True)
                page = context.new_page()
                page.goto(url, wait_until='networkidle', timeout=20000)
                html = page.content()
                browser.close()
                if "Please enable JavaScript" not in html and "Cloudflare" not in html and "human verification" not in html:
                    return html
        except Exception as e:
            log.warning(f"Patchright strategy failed: {e}")

        return ""

class AgenticEvidenceProvider:
    """
    Master Orchestrator. Loops over search results until it finds specs.
    """
    def __init__(self):
        self.scraper = AdaptiveScraperAgent()
        self.extractor = SpecBlockExtractor()

    def fetch(self, mpn: str) -> dict:
        log.info(f"AgenticEvidenceProvider: Orchestrating search for {mpn}")
        urls_to_try = []
        
        # 1. Search Agent
        try:
            with DDGS() as ddgs:
                # Get official and manual sites
                results = list(ddgs.text(f"{mpn} specifications", max_results=5))
                for r in results:
                    href = r.get("href")
                    if href and href not in urls_to_try:
                        urls_to_try.append(href)
        except Exception as e:
            log.error(f"Search Agent failed: {e}")

        if not urls_to_try:
            return None

        # 2. Iterate and Extract
        for url in urls_to_try:
            log.info(f"AgenticEvidenceProvider: Trying URL {url}")
            html = self.scraper.fetch(url)
            if not html:
                continue
                
            # Use unsupervised wrapper induction to find specs
            extracted_facts = self.extractor.extract_pairs(html)
            
            # If we found at least 3 specs, we consider it a success
            if extracted_facts and len(extracted_facts) >= 3:
                log.info(f"AgenticEvidenceProvider: Success! Found {len(extracted_facts)} specs at {url}")
                
                # Bundle the evidence
                evidence_bundle = {
                    "source_url": url,
                    "source_tier": 4, # 4 = Spec Sheet / High confidence web page
                    "facts": {}
                }
                
                for k, v in extracted_facts.items():
                    evidence_bundle["facts"][k] = v
                
                return evidence_bundle

        return None
