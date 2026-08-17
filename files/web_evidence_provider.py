"""
Web Evidence Provider — real-time product data retrieval.

For each MPN, this provider:
1. Searches manufacturer/retailer sites for the product page
2. Fetches the HTML
3. Extracts specification attribute-value pairs using wrapper induction
4. Returns an evidence bundle with real, sourced data

This replaces the hardcoded provider with live web retrieval.
Every fact returned has a traceable URL source — Doc-First compliant.
"""
from __future__ import annotations
import re
import time
import logging
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from evidence_provider import EvidenceProvider
from html_spec_extractor import SpecBlockExtractor
from models import Evidence

log = logging.getLogger(__name__)

# ── Request settings ────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 6
MAX_TIME_PER_MPN = 8.0  # seconds — don't spend more than this per MPN
DELAY_BETWEEN_REQUESTS = 0.3  # seconds — be polite but fast

# ── Manufacturer / retailer search URLs ─────────────────────────────
# Retailer search pages with structured spec tables work best.
# Direct manufacturer search endpoints are second priority.
SEARCH_SOURCES = [
    # Retailer search (fast, structured data)
    ("amazon", "https://www.amazon.com/s?k={mpn}"),
    ("homedepot", "https://www.homedepot.com/s/{mpn}"),
    ("lowes", "https://www.lowes.com/search?searchTerm={mpn}"),
    # Direct manufacturer search
    ("frigidaire", "https://www.frigidaire.com/search?query={mpn}"),
    ("whirlpool", "https://www.whirlpool.com/search.html?query={mpn}"),
    ("lg", "https://www.lg.com/us/search?query={mpn}"),
    ("kitchenaid", "https://www.kitchenaid.com/search.html?query={mpn}"),
    ("maytag", "https://www.maytag.com/search.html?query={mpn}"),
    ("bosch", "https://www.bosch-home.com/us/search.html?query={mpn}"),
    ("ge", "https://www.geappliances.com/search.htm?searchTerm={mpn}"),
]

# ── Attribute extraction patterns (supplement html_spec_extractor) ──
# These are targeted patterns for common appliance spec structures
# that the generic extractor might miss.
EXTRA_PATTERNS = [
    # "Voltage: 120 V" anywhere in text
    (re.compile(r"Voltage\s*[:\-]\s*(\d+)\s*V", re.I), "Voltage Rating", "V"),
    (re.compile(r"(\d+)\s*Volts?", re.I), "Voltage Rating", "V"),
    # "Amperage: 15 A" or "Amps: 15"
    (re.compile(r"Amper(?:age|s)\s*[:\-]\s*(\d+)\s*A?", re.I), "Amperage Rating", "A"),
    (re.compile(r"(\d+)\s*Amps?\b", re.I), "Amperage Rating", "A"),
    # Sound level
    (re.compile(r"(\d+)\s*dBA?\b", re.I), "Sound Level", "dBA"),
    (re.compile(r"Noise\s*[:\-]\s*(\d+)\s*dB", re.I), "Sound Level", "dBA"),
    # Wash cycles
    (re.compile(r"(\d+)\s*(?:wash\s*)?Cycles?", re.I), "Number of Wash Cycles", None),
    (re.compile(r"Cycles?\s*[:\-]\s*(\d+)", re.I), "Number of Wash Cycles", None),
    # Mounting
    (re.compile(r"Built[\s\-]?in", re.I), "Mounting Type", None),
    (re.compile(r"Freestanding", re.I), "Mounting Type", None),
    (re.compile(r"Countertop", re.I), "Mounting Type", None),
    # Material
    (re.compile(r"Stainless\s*Steel", re.I), "Material", None),
    (re.compile(r"(?:Tub|Drum)\s*(?:Material|Finish)\s*[:\-]\s*(\w[\w\s]*)", re.I), "Material", None),
    # Dimensions (Width x Height x Depth)
    (re.compile(r"(\d+(?:-\d+\/\d+)?)\s*(?:in\.?|inch(?:es)?)?\s*[Wx×]\s*(\d+(?:-\d+\/\d+)?)\s*(?:in\.?|inch(?:es)?)?\s*[Dx×]", re.I), "Size", "in"),
    # Sound with range
    (re.compile(r"(\d+)\s*[-–to]+\s*(\d+)\s*dBA", re.I), "Sound Level", "dBA"),
]

# Canonical attribute name mapping (lowercase → canonical)
ATTR_MAP = {
    "voltage": "Voltage Rating",
    "voltage rating": "Voltage Rating",
    "amperage": "Amperage Rating",
    "amperage rating": "Amperage Rating",
    "amps": "Amperage Rating",
    "amp rating": "Amperage Rating",
    "sound level": "Sound Level",
    "decibel level": "Sound Level",
    "noise level": "Sound Level",
    "dba": "Sound Level",
    "material": "Material",
    "tub material": "Material",
    "finish": "Material",
    "mounting": "Mounting Type",
    "mounting type": "Mounting Type",
    "install type": "Mounting Type",
    "size": "Size",
    "dimensions": "Size",
    "product dimensions": "Size",
    "depth": "Depth With Door Open",
    "depth with door open": "Depth With Door Open",
    "wash cycles": "Number of Wash Cycles",
    "number of wash cycles": "Number of Wash Cycles",
    "cycles": "Number of Wash Cycles",
    "cycle count": "Number of Wash Cycles",
    "series": "Series",
    "product series": "Series",
    "color": "Color",
    "colour": "Color",
    "plug type": "Plug Type",
    "power cord": "Plug Type",
    "weight": "Weight",
    "product weight": "Weight",
    "height": "Minimum Height",
    "width": "Width",
    "energy star": "Energy Star",
    "energy rating": "Energy Star",
    "warranty": "Warranty",
}

# Brand/manufacturer inference from page content
KNOWN_BRANDS = {
    "frigidaire": ("FRIGIDAIRE", "Electrolux"),
    "whirlpool": ("Whirlpool", "Whirlpool Corporation"),
    "lg": ("LG", "LG Electronics"),
    "samsung": ("Samsung", "Samsung Electronics"),
    "kitchenaid": ("KitchenAid", "Whirlpool Corporation"),
    "maytag": ("Maytag", "Whirlpool Corporation"),
    "bosch": ("Bosch", "BSH Home Appliances"),
    "ge": ("GE", "GE Appliances"),
    "general electric": ("GE", "GE Appliances"),
    "hotpoint": ("Hotpoint", "GE Appliances"),
    "electrolux": ("Electrolux", "Electrolux"),
    "miele": ("Miele", "Miele"),
    "speed queen": ("Speed Queen", "Alliance Laundry Systems"),
}


class WebEvidenceProvider(EvidenceProvider):
    """
    Real-time web evidence provider.
    
    For each MPN:
    1. Searches known manufacturer/retailer sites
    2. Fetches product pages
    3. Extracts specs using HTML spec extractor + targeted patterns
    4. Returns evidence bundle with traceable sources
    
    Doc-First: never generates values — only extracts what's on the page.
    Graceful degradation: if no page found, returns empty evidence.
    """

    def __init__(self):
        self.spec_extractor = SpecBlockExtractor()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}  # mpn -> evidence bundle
        self._last_request_time = 0.0

    def _throttle(self):
        """Rate-limit requests to be polite to servers."""
        elapsed = time.time() - self._last_request_time
        if elapsed < DELAY_BETWEEN_REQUESTS:
            time.sleep(DELAY_BETWEEN_REQUESTS - elapsed)
        self._last_request_time = time.time()

    def fetch(self, mfg_part_num: str) -> dict:
        """
        Fetch real product evidence for an MPN from the web.
        
        Returns evidence bundle dict, or empty dict if nothing found.
        Enforces MAX_TIME_PER_MPN to prevent hanging on slow sites.
        """
        if mfg_part_num in self._cache:
            return self._cache[mfg_part_num]

        mpn = mfg_part_num.strip().upper()
        log.info(f"Web evidence fetch for MPN: {mpn}")
        start_time = time.time()

        # Try each search source until we find a product page
        for source_name, url_template in SEARCH_SOURCES:
            # Check per-MPN timeout
            if time.time() - start_time > MAX_TIME_PER_MPN:
                log.info(f"  Timeout ({MAX_TIME_PER_MPN}s) reached for {mpn}")
                break
                
            try:
                search_url = url_template.format(mpn=quote_plus(mpn))
                self._throttle()
                
                resp = self.session.get(search_url, timeout=TIMEOUT, allow_redirects=True)
                if resp.status_code != 200:
                    log.debug(f"  {source_name}: HTTP {resp.status_code}")
                    continue

                html = resp.text
                if len(html) < 500:
                    log.debug(f"  {source_name}: page too small ({len(html)} bytes)")
                    continue

                # Check if the page actually contains our MPN
                if mpn.lower() not in html.lower():
                    log.debug(f"  {source_name}: MPN not found in page content")
                    continue

                # Found a relevant page — extract specs
                bundle = self._extract_from_html(html, mpn, source_name, resp.url)
                if bundle:
                    log.info(f"  {source_name}: extracted {len(bundle.get('facts', {}))} attributes")
                    self._cache[mfg_part_num] = bundle
                    return bundle
                else:
                    log.debug(f"  {source_name}: no specs extracted")

            except requests.RequestException as e:
                log.debug(f"  {source_name}: request failed: {e}")
                continue
            except Exception as e:
                log.debug(f"  {source_name}: extraction failed: {e}")
                continue

        log.info(f"  No evidence found for {mpn}")
        return {}

    def _extract_from_html(
        self, html: str, mpn: str, source_name: str, page_url: str
    ) -> Optional[dict]:
        """
        Extract product evidence from fetched HTML.
        
        Uses two extraction methods:
        1. HTML spec extractor (Paper 2 wrapper induction)
        2. Targeted regex patterns for common appliance specs
        
        Returns evidence bundle or None if nothing useful found.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove noise elements
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        cleaned_html = str(soup)
        
        # Method 1: Generic spec extractor (Paper 2)
        generic_specs = self.spec_extractor.extract_pairs(cleaned_html)
        
        # Method 2: Targeted regex patterns
        text = soup.get_text(separator=" ", strip=True)
        targeted_specs = self._extract_targeted(text, mpn)
        
        # Merge: targeted takes priority over generic
        all_specs = {}
        all_specs.update(generic_specs)
        all_specs.update(targeted_specs)
        
        # Map to canonical attribute names and build evidence bundle
        facts = {}
        for raw_attr, (value, uom, ev) in all_specs.items():
            canonical = self._canonicalize(raw_attr)
            if canonical and value:
                # Override evidence source with actual page URL
                ev.source_url = page_url
                ev.page_or_section = f"web fetch from {source_name}"
                facts[canonical] = (value, uom, ev)

        if not facts:
            return None

        # Infer brand/manufacturer from page
        brand_name, manufacturer = self._infer_brand(cleaned_html, source_name)
        series = self._extract_series(text)

        return {
            "_manufacturer_name": manufacturer or source_name.title(),
            "_brand_name": brand_name or mpn,
            "_series": series,
            "_mfr_url": page_url,
            "facts": facts,
        }

    def _extract_targeted(self, text: str, mpn: str) -> dict:
        """Apply targeted regex patterns to raw text."""
        results = {}
        for pattern, attr_label, uom in EXTRA_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if groups:
                    value = groups[0].strip()
                else:
                    # For patterns that just detect presence (e.g., "Built-in")
                    value = match.group(0).strip()
                
                if value and attr_label not in results:
                    ev = Evidence(
                        source_url="web_fetch",
                        source_tier=3,
                        page_or_section="targeted regex extraction",
                    )
                    # Normalize value for certain attributes
                    if attr_label == "Material" and "stainless" in value.lower():
                        value = "Stainless Steel"
                    elif attr_label == "Mounting Type":
                        if "built" in value.lower():
                            value = "Built-in"
                        elif "free" in value.lower():
                            value = "Freestanding"
                    elif attr_label == "Mounting Type" and "leg" in value.lower():
                        value = "Leg"
                    
                    results[attr_label] = (value, uom, ev)

        return results

    def _canonicalize(self, raw_name: str) -> Optional[str]:
        """Map raw attribute name to canonical label."""
        lower = raw_name.lower().strip()
        return ATTR_MAP.get(lower)

    def _infer_brand(self, html: str, source_name: str) -> tuple[Optional[str], Optional[str]]:
        """Infer brand and manufacturer from page HTML."""
        html_lower = html.lower()
        
        for keyword, (brand, mfr) in KNOWN_BRANDS.items():
            if keyword in html_lower:
                return brand, mfr
        
        # Fallback: try to find brand in common meta tags
        soup = BeautifulSoup(html, "html.parser")
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"]
            for keyword, (brand, mfr) in KNOWN_BRANDS.items():
                if keyword in title.lower():
                    return brand, mfr
        
        return None, None

    def _extract_series(self, text: str) -> Optional[str]:
        """Try to extract product series from text."""
        series_patterns = [
            re.compile(r"Series\s*[:\-]?\s*([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)", re.I),
            re.compile(r"((?:Eco|Professional|Ultra|Premium|Standard|Elite|Platinum)\s*Series)", re.I),
        ]
        for pat in series_patterns:
            match = pat.search(text)
            if match:
                return match.group(0).strip().rstrip(".,")
        return None
