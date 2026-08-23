import ipaddress
import logging
import socket
import time
from urllib.parse import urlparse

import requests
from ddgs import DDGS
from patchright.sync_api import sync_playwright
from html_spec_extractor import SpecBlockExtractor

log = logging.getLogger(__name__)


def _is_safe_external_url(url: str) -> bool:
    """This scraper fetches URLs discovered via live search results — attacker-
    influenced input, in principle (a crafted/indexed page, a poisoned search
    result). Refuse anything that isn't a plain http(s) request to a public
    host, so a malicious search hit can't make this server request its own
    internal services, localhost, or cloud metadata endpoints (SSRF)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host:
            return False
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            # Hostname, not a literal IP — resolve it before judging safety.
            addr = ipaddress.ip_address(socket.gethostbyname(host))
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            return False
        return True
    except Exception:
        # If we can't resolve/parse it confidently, don't fetch it.
        return False

# Unilog's solution guide explicitly forbids sourcing from marketplaces and
# distributor sites ("Marketplaces and distributor sites are explicitly
# excluded... no marketplace/distributor data sourcing"). A raw web search
# for an MPN routinely surfaces exactly these, so every result is filtered
# against this list before it's ever fetched.
EXCLUDED_DOMAINS = (
    "amazon.", "ebay.", "walmart.", "homedepot.", "lowes.", "wayfair.",
    "target.", "grainger.", "zoro.", "mcmaster.", "globalindustrial.",
    "mscdirect.", "acmetools.", "supplyhouse.", "ferguson.", "build.com",
    "webstaurantstore.", "alibaba.", "aliexpress.", "etsy.", "houzz.",
    "overstock.", "newegg.", "bestbuy.", "menards.", "acehardware.",
    "harborfreight.", "northerntool.", "toolnut.", "cpo", "sears.",
)


def _is_excluded_source(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in EXCLUDED_DOMAINS)


# Wall-clock budget for one MPN's worth of live search + scraping. Real
# network calls take real time, but an unbounded loop over N search results
# (each with a Wayback + requests + full headless-browser fallback chain)
# can blow past any per-row timeout the caller enforces.
AGENTIC_MAX_TIME_PER_MPN = 12.0

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

    def fetch(self, url: str, mpn: str = "") -> str:
        return self.fetch_with_url(url, mpn)[0]

    def fetch_with_url(self, url: str, mpn: str = "") -> tuple[str, str]:
        """Fetch HTML for a URL, returning (html, final_url).

        If `mpn` is given and the page is a search/listing page, tries to
        click through to the matching product page (requires Patchright,
        since a plain HTTP GET cannot execute the click).
        """
        if not _is_safe_external_url(url):
            log.warning(f"AdaptiveScraperAgent: refusing to fetch unsafe/internal URL {url}")
            return "", url

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
                        return r.text, snapshot_url
            except Exception as e:
                log.warning(f"Wayback Machine strategy failed: {e}")

        # Strategy 2: Standard Requests (fastest) — only good enough if the
        # MPN is already present (i.e. not a search page we'd need to click through).
        try:
            log.info(f"AdaptiveScraperAgent: Trying standard requests for {url}")
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200 and len(r.text) > 5000:
                clean = ("Please enable JavaScript" not in r.text and "Cloudflare" not in r.text
                         and "human verification" not in r.text)
                if clean and (not mpn or mpn.lower() in r.text.lower()):
                    return r.text, r.url
        except Exception:
            pass

        # Strategy 3: Patchright Stealth — can click through search results to
        # reach the real product page (JS-rendered listings, search forms).
        try:
            log.info(f"AdaptiveScraperAgent: Trying Patchright for {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.headers['User-Agent'], ignore_https_errors=True)
                page = context.new_page()
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=10000)
                except Exception:
                    pass  # DOM may still be usable even if load never fully completes

                if mpn and mpn.lower() not in page.content().lower():
                    pass  # nothing to click if MPN isn't referenced anywhere
                elif mpn:
                    try:
                        locator = page.locator(f'a:has-text("{mpn}"), a[href*="{mpn.lower()}"]').first
                        if locator.is_visible(timeout=2000):
                            locator.click(timeout=4000)
                            page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except Exception:
                        pass  # stay on the current page if no clickable result found

                html = page.content()
                final_url = page.url
                browser.close()
                if "Please enable JavaScript" not in html and "Cloudflare" not in html and "human verification" not in html:
                    return html, final_url
        except Exception as e:
            log.warning(f"Patchright strategy failed: {e}")

        return "", url

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
        
        # 1. Search Agent — request extra results since marketplace/distributor
        # hits (forbidden as sources) get filtered out below.
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{mpn} specifications", max_results=10))
                for r in results:
                    href = r.get("href")
                    if href and href not in urls_to_try and not _is_excluded_source(href):
                        urls_to_try.append(href)
                    elif href and _is_excluded_source(href):
                        log.info(f"AgenticEvidenceProvider: skipping forbidden marketplace/distributor source {href}")
        except Exception as e:
            log.error(f"Search Agent failed: {e}")

        if not urls_to_try:
            return None

        # 2. Iterate and Extract
        start_time = time.time()
        for url in urls_to_try:
            if time.time() - start_time > AGENTIC_MAX_TIME_PER_MPN:
                log.info(f"AgenticEvidenceProvider: time budget exceeded for {mpn}, stopping search")
                break
            log.info(f"AgenticEvidenceProvider: Trying URL {url}")
            html, real_url = self.scraper.fetch_with_url(url, mpn)
            if not html:
                continue
                
            # Use unsupervised wrapper induction to find specs
            extracted_facts = self.extractor.extract_pairs(html)
            
            # If we found at least 3 specs, we consider it a success
            if extracted_facts and len(extracted_facts) >= 3:
                log.info(f"AgenticEvidenceProvider: Success! Found {len(extracted_facts)} specs at {url}")
                
                # Bundle the evidence
                evidence_bundle = {
                    "source_url": real_url,
                    "source_tier": 4, # 4 = Spec Sheet / High confidence web page
                    "facts": {}
                }
                
                for k, v in extracted_facts.items():
                    evidence_bundle["facts"][k] = v
                
                return evidence_bundle

        return None
