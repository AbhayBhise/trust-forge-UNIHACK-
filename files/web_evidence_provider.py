"""
Web Evidence Provider — real-time product data retrieval.

For each MPN, this provider:
1. Searches manufacturer/retailer sites for the product page
2. Fetches the HTML
3. Extracts specification attribute-value pairs using wrapper induction
4. Returns an evidence bundle with real, sourced data

This replaces the hardcoded provider with live web retrieval.
Every fact returned has a traceable URL source — Doc-First compliant.

Caching: Results are persisted to web_evidence_cache.json between runs.
Second time processing the same MPNs takes milliseconds, not seconds.
"""
from __future__ import annotations
import json
import os
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
from activity_tracker import tracker
from agentic_provider import AdaptiveScraperAgent

log = logging.getLogger(__name__)

# ── Cache file ───────────────────────────────────────────────────────
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_evidence_cache.json")

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
TIMEOUT = 4
MAX_TIME_PER_MPN = 12.0  # seconds — now only tries 2 targeted URLs (no more blind 28-site guessing)
DELAY_BETWEEN_REQUESTS = 0.2  # seconds — reduced from 0.3s

# ── Manufacturer search URLs ─────────────────────────────
# Direct manufacturer search endpoints. E-commerce sites are forbidden.
# Expanded to cover major appliance and tool manufacturers.
SEARCH_SOURCES = [
    # Major Appliance Manufacturers
    ("frigidaire", "https://www.frigidaire.com/search?query={mpn}"),
    ("whirlpool", "https://www.whirlpool.com/search.html?query={mpn}"),
    ("lg", "https://www.lg.com/us/search?query={mpn}"),
    ("kitchenaid", "https://www.kitchenaid.com/search.html?query={mpn}"),
    ("maytag", "https://www.maytag.com/search.html?query={mpn}"),
    ("ge", "https://www.geappliances.com/appliance/{mpn}"),
    ("samsung", "https://www.samsung.com/us/search/searchMain/?query={mpn}"),
    ("bosch_home", "https://www.bosch-home.com/us/search/?q={mpn}"),
    ("miele", "https://www.miele.com/en-us/search.html?q={mpn}"),
    ("speed_queen", "https://www.speedqueen.com/search/?q={mpn}"),
    ("hotpoint", "https://www.hotpoint.com/search.html?query={mpn}"),
    ("electrolux", "https://www.electrolux.com/search?query={mpn}"),
    ("haier", "https://www.haier.com/us/search/?q={mpn}"),
    ("Sharp", "https://www.sharpusa.com/search?q={mpn}"),
    # Tool Manufacturers
    ("bosch_tools", "https://www.boschtools.com/us/en/search/?q={mpn}"),
    ("mirka", "https://www.mirka.com/en-US/search?q={mpn}"),
    ("milwaukee", "https://www.milwaukeetool.com/search?q={mpn}"),
    ("dewalt", "https://www.dewalt.com/search?q={mpn}"),
    ("makita", "https://www.makitatools.com/search?q={mpn}"),
    ("festool", "https://www.festoolusa.com/search?q={mpn}"),
    ("ridgid", "https://www.ridgid.com/us/en/search?q={mpn}"),
    ("craftsman", "https://www.craftsman.com/search?q={mpn}"),
    # Plumbing / Electrical
    ("moen", "https://www.moen.com/search?q={mpn}"),
    ("delta", "https://www.deltafaucet.com/search?q={mpn}"),
    ("kohler", "https://www.kohler.com/en/search?query={mpn}"),
    ("leviton", "https://www.leviton.com/search?q={mpn}"),
    ("lutron", "https://www.lutron.com/en-us/search?q={mpn}"),
]

# ── Brand name → manufacturer domain mapping ──────────────────────────
# Used when the input CSV has a distributor as Part_Manuf, we need to
# map to the actual manufacturer's website for evidence retrieval.
BRAND_DOMAINS = {
    # Appliance brands
    "frigidaire": "frigidaire.com",
    "whirlpool": "whirlpool.com",
    "kitchenaid": "kitchenaid.com",
    "maytag": "maytag.com",
    "ge appliances": "geappliances.com",
    "general electric": "geappliances.com",
    "hotpoint": "hotpoint.com",
    "electrolux": "electrolux.com",
    "lg electronics": "lg.com",
    "samsung": "samsung.com",
    "bosch": "bosch-home.com",
    "miele": "miele.com",
    "speed queen": "speedqueen.com",
    "haier": "haier.com",
    "sharp": "sharpusa.com",
    # Tool brands
    "bosch": "boschtools.com",
    "mirka abrasives inc": "mirka.com",
    "mirka": "mirka.com",
    "milwaukee accessory": "milwaukeetool.com",
    "milwaukee tool": "milwaukeetool.com",
    "black & decker/dewlt": "dewalt.com",
    "dewalt": "dewalt.com",
    "makita usa inc": "makitatools.com",
    "makita": "makitatools.com",
    "festool usa": "festoolusa.com",
    "festool": "festoolusa.com",
    "ridgid": "ridgid.com",
    "craftsman": "craftsman.com",
    # Plumbing brands
    "moen": "moen.com",
    "delta": "deltafaucet.com",
    "kohler": "kohler.com",
    # Electrical brands
    "leviton mfg co": "leviton.com",
    "leviton": "leviton.com",
    "lutron": "lutron.com",
    "phillips lighting": "signify.com",
    "satco prod inc": "satco.com",
    "kichler lighting": "kichler.com",
    # Other
    "3m": "3m.com",
    "southwire/g turner": "southwire.com",
    "freud inc": "freudtools.com",
    "kreg tool company": "kregtool.com",
    "parksite": "parksite.com",
    "u s lumber": "uslumber.com",
    "u s tape company": "ustape.com",
    "boise cascade building materials": "bc.com",
}

# ── Attribute extraction patterns (supplement html_spec_extractor) ──
# Comprehensive patterns for extracting specs from manufacturer pages.
# These cover appliances, tools, plumbing, electrical, and building materials.
EXTRA_PATTERNS = [
    # Voltage
    (re.compile(r"Voltage\s*[:\-]\s*(\d+)\s*V", re.I), "Voltage Rating", "V"),
    (re.compile(r"(\d+)\s*Volts?", re.I), "Voltage Rating", "V"),
    (re.compile(r"(\d+)\s*v\b", re.I), "Voltage Rating", "V"),
    # Amperage
    (re.compile(r"Amper(?:age|s)\s*[:\-]\s*(\d+)\s*A?", re.I), "Amperage Rating", "A"),
    (re.compile(r"(\d+)\s*Amps?\b", re.I), "Amperage Rating", "A"),
    (re.compile(r"(\d+)\s*A\b", re.I), "Amperage Rating", "A"),
    # Sound level
    (re.compile(r"(\d+)\s*dBA?\b", re.I), "Sound Level", "dBA"),
    (re.compile(r"Noise\s*[:\-]\s*(\d+)\s*dB", re.I), "Sound Level", "dBA"),
    (re.compile(r"Decibel\s*(?:Level)?\s*[:\-]\s*(\d+)", re.I), "Sound Level", "dBA"),
    # Wash cycles
    (re.compile(r"(\d+)\s*(?:wash\s*)?Cycles?", re.I), "Number of Wash Cycles", None),
    (re.compile(r"Cycles?\s*[:\-]\s*(\d+)", re.I), "Number of Wash Cycles", None),
    # Mounting
    (re.compile(r"Built[\s\-]?in", re.I), "Mounting Type", None),
    (re.compile(r"Freestanding", re.I), "Mounting Type", None),
    (re.compile(r"Countertop", re.I), "Mounting Type", None),
    (re.compile(r"Top[\s\-]Load", re.I), "Mounting Type", None),
    (re.compile(r"Front[\s\-]Load", re.I), "Mounting Type", None),
    (re.compile(r"Under[\s\-]?counter", re.I), "Mounting Type", None),
    (re.compile(r"Deck\s*Mount", re.I), "Mounting Type", None),
    (re.compile(r"Wall\s*Mount", re.I), "Mounting Type", None),
    # Material / finish — prefer tub/interior material
    (re.compile(r"(?:Tub|Drum|Interior)\s*(?:Material|Finish)\s*[:\-]\s*([\w\s]+?)(?:\.|,|;|$)", re.I), "Material", None),
    (re.compile(r"Stainless\s*Steel", re.I), "Material", None),
    (re.compile(r"Material\s*[:\-]\s*(Stainless\s*Steel|Plastic|Porcelain|Glass|Aluminum|Steel|Brass|Copper|Cast\s*Iron|Ceramic)", re.I), "Material", None),
    # Color
    (re.compile(r"(?:Color|Colour|Finish)\s*[:\-]\s*(Stainless Steel|White|Black|Slate|Graphite|Bisque|Black Stainless|Silver|Matte Black|Gray|Platinum|Chrome|Brushed Nickel|Oil Rubbed Bronze|Polished Brass)", re.I), "Color", None),
    # Dimensions — H x W x D format
    (re.compile(r"(\d+(?:[\-–]\d+/\d+)?)\s*in\.?\s*H\s*[x×]\s*(\d+(?:[\-–]\d+/\d+)?)\s*in\.?\s*W\s*[x×]\s*(\d+(?:[\-–]\d+/\d+)?)\s*in\.?\s*D", re.I), "Size", "in"),
    # Partial dimensions
    (re.compile(r"(\d+(?:[\-–]\d+/\d+)?)\s*in\.?\s*W\s*[x×]\s*(\d+(?:[\-–]\d+/\d+)?)\s*in\.?\s*D", re.I), "Size", "in"),
    # Depth with door open
    (re.compile(r"(?:Depth\s+[Ww]ith\s+[Dd]oor\s+[Oo]pen|With\s+[Dd]oor\s+[Oo]pen)\s*[:\-]?\s*(\d+(?:[\-–]\d+/\d+)?)\s*(?:in\.?|inch)?", re.I), "Depth With Door Open", "in"),
    # Energy/Annual energy
    (re.compile(r"(\d+)\s*kWh?[\-\s]?(?:per\s+year|annual|yr)", re.I), "Energy Use", "kWh"),
    # Delay start
    (re.compile(r"(\d+)\s*(?:to|-)?\s*(\d+)\s*[Hh](?:our)?\s*[Dd]elay", re.I), "Delay Start", "hr"),
    # Sound with range
    (re.compile(r"(\d+)\s*[-–to]+\s*(\d+)\s*dBA", re.I), "Sound Level", "dBA"),
    # Wattage
    (re.compile(r"Watt(?:age)?\s*[:\-]\s*(\d+)\s*W", re.I), "Wattage", "W"),
    (re.compile(r"(\d+)\s*W(?:atts?)?\b", re.I), "Wattage", "W"),
    # Flow Rate (faucets)
    (re.compile(r"Flow\s*Rate\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(?:gpm|GPM)", re.I), "Flow Rate", "gpm"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*gpm\b", re.I), "Flow Rate", "gpm"),
    # Number of Handles (faucets)
    (re.compile(r"(\d+)\s*Handle", re.I), "Number of Handles", None),
    # Pipe Size (fittings)
    (re.compile(r"(?:Pipe|Tube)\s*Size\s*[:\-]\s*([\d/\-]+)\s*(?:in\.?|inch)?", re.I), "Pipe Size", "in"),
    (re.compile(r"(\d+(?:/\d+)?)\s*(?:in\.?|inch)\s*(?:NPT|Pipe)", re.I), "Pipe Size", "in"),
    # Maximum Pressure (fittings)
    (re.compile(r"(?:Max(?:imum)?)?\s*Pressure\s*[:\-]\s*(\d+)\s*(?:psi|PSI)", re.I), "Maximum Pressure", "psi"),
    (re.compile(r"(\d+)\s*psi\b", re.I), "Maximum Pressure", "psi"),
    # Weight
    (re.compile(r"Weight\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(?:lb|lbs?|pound)", re.I), "Weight", "lb"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs?)\b", re.I), "Weight", "lb"),
    # Warranty
    (re.compile(r"Warranty\s*[:\-]\s*(.+?)(?:\.|$)", re.I), "Warranty", None),
    # Model Number
    (re.compile(r"Model\s*(?:Number|No\.?)?\s*[:\-]\s*([A-Z0-9\-]+)", re.I), "Model", None),
    # EAN/UPC
    (re.compile(r"(?:EAN|UPC|GTIN)\s*[:\-]?\s*(\d{12,14})", re.I), "EAN/UPC", None),
    # Series
    (re.compile(r"Series\s*[:\-]?\s*([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)", re.I), "Series", None),
    (re.compile(r"((?:Eco|Professional|Ultra|Premium|Standard|Elite|Platinum|Signature|Heritage|Classic)\s*Series)", re.I), "Series", None),
    # Energy Star
    (re.compile(r"ENERGY\s*STAR", re.I), "Energy Star", None),
]

# Canonical attribute name mapping (lowercase → canonical)
# Comprehensive mapping covering appliances, tools, plumbing, electrical
ATTR_MAP = {
    # Electrical
    "voltage": "Voltage Rating", "voltage rating": "Voltage Rating",
    "voltage (v)": "Voltage Rating", "electrical rating": "Voltage Rating",
    "amperage": "Amperage Rating", "amperage rating": "Amperage Rating",
    "amps": "Amperage Rating", "amp rating": "Amperage Rating",
    "amperage (a)": "Amperage Rating", "current": "Amperage Rating",
    # Sound
    "sound level": "Sound Level", "decibel level": "Sound Level",
    "noise level": "Sound Level", "dba": "Sound Level",
    "noise": "Sound Level", "sound": "Sound Level",
    # Material
    "material": "Material", "tub material": "Material",
    "finish": "Material", "drum material": "Material",
    "interior material": "Material", "body material": "Material",
    # Mounting
    "mounting": "Mounting Type", "mounting type": "Mounting Type",
    "install type": "Mounting Type", "installation type": "Mounting Type",
    "mount": "Mounting Type", "setup": "Mounting Type",
    # Dimensions
    "size": "Size", "dimensions": "Size", "product dimensions": "Size",
    "product size": "Size", "overall dimensions": "Size",
    "height": "Minimum Height", "min height": "Minimum Height",
    "minimum height": "Minimum Height", "product height": "Minimum Height",
    "max height": "Maximum Height", "maximum height": "Maximum Height",
    "adjustable height": "Maximum Height",
    "width": "Size", "product width": "Size",
    "depth": "Depth With Door Open", "depth with door open": "Depth With Door Open",
    "depth (door open)": "Depth With Door Open",
    # Cycles
    "wash cycles": "Number of Wash Cycles", "number of wash cycles": "Number of Wash Cycles",
    "cycles": "Number of Wash Cycles", "cycle count": "Number of Wash Cycles",
    "number of cycles": "Number of Wash Cycles",
    # Series
    "series": "Series", "product series": "Series", "product line": "Series",
    # Model
    "model": "Model", "model number": "Model", "model name": "Model",
    "mfg part num": "Model", "product model": "Model",
    # Color
    "color": "Color", "colour": "Color", "finish color": "Color",
    "exterior color": "Color",
    # Power
    "plug type": "Plug Type", "power cord": "Plug Type", "plug": "Plug Type",
    "wattage": "Wattage", "power": "Wattage", "watts": "Wattage",
    # Weight
    "weight": "Weight", "product weight": "Weight", "net weight": "Weight",
    # Energy
    "energy star": "Energy Star", "energy rating": "Energy Star",
    "energy use": "Additional Information", "energy consumption": "Additional Information",
    # Flow (faucets)
    "flow rate": "Flow Rate", "water flow": "Flow Rate",
    # Handles (faucets)
    "handles": "Number of Handles", "number of handles": "Number of Handles",
    "handle type": "Handle Type",
    # Fittings
    "fitting type": "Fitting Type", "type": "Fitting Type",
    "connection type": "Connection Type 1", "pipe size": "Pipe Size",
    "schedule": "Schedule", "max pressure": "Maximum Pressure",
    "maximum pressure": "Maximum Pressure",
    # Warranty
    "warranty": "Warranty", "warranty information": "Warranty",
    # UPC/EAN
    "ean": "EAN/UPC", "upc": "EAN/UPC", "gtin": "EAN/UPC",
    "ean/upc": "EAN/UPC", "barcode": "EAN/UPC",
    # Additional
    "additional information": "Additional Information",
    "features": "Additional Information", "feature": "Additional Information",
    "description": "Additional Information",
    # Faucet specific
    "faucet type": "Faucet Type", "spout type": "Spout Type",
    "spout reach": "Spout Reach", "spout height": "Spout Height",
    "valve type": "Valve Type", "connection size": "Connection Size",
    "ada compliant": "ADA Compliant",
    "delay start": "Additional Information",
}

# Brand/manufacturer inference from page content
KNOWN_BRANDS = {
    # Appliance brands
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
    "haier": ("Haier", "Haier"),
    "sharp": ("Sharp", "Sharp Electronics"),
    # Tool brands
    "dewalt": ("DEWALT", "Stanley Black & Decker"),
    "milwaukee": ("Milwaukee", "Techtronic Industries"),
    "makita": ("Makita", "Makita USA"),
    "festool": ("Festool", "Festool USA"),
    "ridgid": ("Ridgid", "Emerson Electric"),
    "craftsman": ("Craftsman", "Stanley Black & Decker"),
    "bosch tools": ("Bosch", "Robert Bosch Tool Corporation"),
    # Plumbing brands
    "moen": ("Moen", "Fortune Brands Innovations"),
    "delta": ("Delta", "Masco Corporation"),
    "kohler": ("Kohler", "Kohler Co"),
    # Electrical brands
    "leviton": ("Leviton", "Leviton Manufacturing"),
    "lutron": ("Lutron", "Lutron Electronics"),
    "3m": ("3M", "3M Company"),
    "southwire": ("Southwire", "Southwire Company"),
    # Abrasives / cutting brands
    "diablo": ("Diablo", "Freud Inc"),
    "freud": ("Freud", "Freud Inc"),
    "mirka": ("Mirka", "Mirka Abrasives Inc"),
    "norton": ("Norton", "Saint-Gobain Abrasives"),
    # Decking / lumber brands
    "trex": ("Trex", "Trex Company"),
    "azek": ("Azek", "AZEK Building Products"),
    "timbertech": ("TimberTech", "AZEK Building Products"),
    # Hardware / fasteners
    "national nail": ("National Nail", "National Nail Corp"),
    "matco-norca": ("Matco-Norca", "Matco-Norca Inc"),
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
        self.scraper = AdaptiveScraperAgent()
        self._cache = {}  # mpn -> evidence bundle (in-memory)
        self._last_request_time = 0.0
        self._load_cache()

    def _load_cache(self):
        """Load persistent cache from disk (instant for repeat runs)."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                log.info(f"Loaded {len(self._cache)} cached MPNs from disk")
            except Exception:
                self._cache = {}

    def _save_cache(self):
        """Persist cache to disk (survives server restarts)."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _throttle(self):
        """Rate-limit requests to be polite to servers."""
        elapsed = time.time() - self._last_request_time
        if elapsed < DELAY_BETWEEN_REQUESTS:
            time.sleep(DELAY_BETWEEN_REQUESTS - elapsed)
        self._last_request_time = time.time()

    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        brand = row.get("MANUFACTURER_NAME", row.get("Part_Manuf", ""))
        desc = row.get("Part_Desc", "")
        return self._fetch_internal(mfg_part_num, brand, desc)

    def fetch(self, mfg_part_num: str) -> dict:
        return self._fetch_internal(mfg_part_num, "", "")

    def _resolve_brand_domain(self, brand: str, desc: str) -> Optional[tuple[str, str]]:
        """Find a known manufacturer domain from an explicit brand field or,
        failing that, from a brand keyword actually present in the product
        description. Never guesses — returns None if there's no real signal,
        so callers don't fall back to blindly trying unrelated manufacturer
        sites (which produces false positives when a site's own "no results
        for '<query>'" text happens to contain the MPN)."""
        brand_lower = brand.lower() if brand else ""
        brand_lower = re.sub(r'\s*\([^)]*\)', '', brand_lower).strip()
        if brand_lower in BRAND_DOMAINS:
            return brand_lower, BRAND_DOMAINS[brand_lower]

        desc_lower = (desc or "").lower()
        if desc_lower:
            # Longest keys first so e.g. "bosch tools" wins over "bosch".
            for key in sorted(BRAND_DOMAINS.keys(), key=len, reverse=True):
                if re.search(r'\b' + re.escape(key) + r'\b', desc_lower):
                    return key, BRAND_DOMAINS[key]
        return None

    def _fetch_internal(self, mfg_part_num: str, brand: str, desc: str = "") -> dict:
        """
        Fetch real product evidence for an MPN from the web.

        Returns evidence bundle dict, or empty dict if nothing found.
        Enforces MAX_TIME_PER_MPN to prevent hanging on slow sites.
        """
        if mfg_part_num in self._cache:
            tracker.emit(
                mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                action="cache_hit", detail=f"Cache hit for {mfg_part_num} — skipping web fetch",
                icon="done", status="success",
            )
            return self._cache[mfg_part_num]

        mpn = mfg_part_num.strip().upper()
        log.info(f"Web evidence fetch for MPN: {mpn} (Brand: {brand})")
        start_time = time.time()

        resolved = self._resolve_brand_domain(brand, desc)
        urls_to_try = []
        if resolved:
            matched_key, domain = resolved
            urls_to_try.append((f"{matched_key}_search", f"https://www.{domain}/search?q={quote_plus(mpn)}"))
            urls_to_try.append((f"{matched_key}_search_alt", f"https://www.{domain}/products/{quote_plus(mpn)}"))
            tracker.emit(
                mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                action="targeted", detail=f"Brand '{matched_key}' resolved to {domain} — trying direct URLs",
                icon="search", status="running",
            )
        else:
            # No real signal for which manufacturer this is — don't blindly
            # guess across unrelated sites. Let AgenticEvidenceProvider's real
            # web search handle it instead.
            tracker.emit(
                mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                action="skip", detail=f"No known brand/domain signal for {mfg_part_num} — deferring to live search",
                icon="arrow", status="skip",
            )
            return {}

        # Try each search source until we find a product page
        for source_name, search_url in urls_to_try:
            if time.time() - start_time > MAX_TIME_PER_MPN:
                tracker.emit(
                    mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                    action="timeout", detail=f"Timeout ({MAX_TIME_PER_MPN}s) reached after trying {source_name}",
                    icon="error", status="fail",
                )
                log.info(f"  Timeout ({MAX_TIME_PER_MPN}s) reached for {mpn}")
                break
                
            self._throttle()
            
            try:
                tracker.emit(
                    mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                    action="fetching", detail=f"Fetching {search_url[:80]}...",
                    icon="fetch", status="running",
                )
                html, real_url = self.scraper.fetch_with_url(search_url, mpn)
                    
                is_search_url = "search" in search_url.lower() or "query" in search_url.lower() or "?q=" in search_url.lower()
                if is_search_url and real_url == search_url:
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="skip", detail=f"{source_name}: still on search page — skipping",
                        icon="arrow", status="skip",
                    )
                    log.debug(f"  {source_name}: failed to navigate to product page (still on search page)")
                    continue

                if len(html) < 500:
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="skip", detail=f"{source_name}: page too small ({len(html)} bytes)",
                        icon="arrow", status="skip",
                    )
                    log.debug(f"  {source_name}: page too small ({len(html)} bytes)")
                    continue

                html_lower = html.lower()
                no_results_markers = (
                    "no results", "0 results", "no matches", "did not match",
                    "we couldn't find", "we could not find", "no products found",
                )
                # An MPN can appear in an unhelpful page purely because the site
                # echoes the raw query back (e.g. "No results found for '<mpn>'").
                # Guard against treating that as a real product match.
                if any(marker in html_lower for marker in no_results_markers):
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="skip", detail=f"{source_name}: page reports no results — not a real product match",
                        icon="arrow", status="skip",
                    )
                    log.debug(f"  {source_name}: no-results page, rejecting")
                    continue

                if mpn.lower() not in html_lower:
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="skip", detail=f"{source_name}: MPN not found in page content",
                        icon="arrow", status="skip",
                    )
                    log.debug(f"  {source_name}: MPN not found in page content")
                    continue

                tracker.emit(
                    mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                    action="extracting", detail=f"{source_name}: MPN found — extracting specs...",
                    icon="extract", status="running",
                )
                bundle = self._extract_from_html(html, mpn, source_name, real_url)
                if bundle:
                    n_facts = len(bundle.get('facts', {}))
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="found", detail=f"{source_name}: {n_facts} attributes extracted from {real_url[:60]}",
                        icon="done", status="success",
                    )
                    log.info(f"  {source_name}: extracted {n_facts} attributes")
                    self._cache[mfg_part_num] = bundle
                    self._save_cache()
                    return bundle
                else:
                    tracker.emit(
                        mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                        action="skip", detail=f"{source_name}: no specs extracted from page",
                        icon="arrow", status="skip",
                    )
                    log.debug(f"  {source_name}: no specs extracted")

            except Exception as e:
                tracker.emit(
                    mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
                    action="error", detail=f"{source_name}: fetch failed — {str(e)[:60]}",
                    icon="error", status="fail",
                )
                log.debug(f"  {source_name}: fetch/extract failed: {e}")
                continue

        tracker.emit(
            mpn=mfg_part_num, step="web_fetch", provider="WebEvidenceProvider",
            action="exhausted", detail=f"All {len(urls_to_try)} sources exhausted for {mpn}",
            icon="error", status="fail",
        )
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
        
        # Method 3: Hunt for PDF spec sheets on the page
        pdf_urls = self._find_pdf_links(soup, page_url)
        for pdf_url in pdf_urls[:2]:  # Try top 2 PDFs
            try:
                self._throttle()
                pdf_resp = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT)
                if pdf_resp.status_code == 200 and len(pdf_resp.content) > 1000:
                    import fitz  # PyMuPDF
                    doc = fitz.open(stream=pdf_resp.content, filetype="pdf")
                    pdf_text = ""
                    for page in doc:
                        pdf_text += page.get_text()
                    doc.close()
                    # Extract from PDF text
                    pdf_specs = self._extract_targeted(pdf_text, mpn)
                    for attr_label, (value, uom, ev) in pdf_specs.items():
                        canonical = self._canonicalize(attr_label)
                        if canonical and value and canonical not in all_specs:
                            ev.source_url = pdf_url
                            ev.source_tier = 5  # PDF = highest tier
                            ev.page_or_section = "PDF spec sheet"
                            all_specs[canonical] = (value, uom, ev)
                    if pdf_text:
                        log.info(f"  PDF extracted from: {pdf_url}")
            except Exception as e:
                log.debug(f"  PDF fetch failed: {pdf_url}: {e}")

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
        with_phrase = self._extract_with_phrase(text)
        approvals = self._extract_approvals(text)

        return {
            "_manufacturer_name": manufacturer or source_name.title(),
            "_brand_name": brand_name or mpn,
            "_series": series,
            "_mfr_url": page_url,
            "_with_phrase": with_phrase,
            "_approvals": approvals,
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
                        source_tier=5,
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
        """Infer brand and manufacturer from page HTML.

        Short brand keys like "lg", "ge", "3m" are a real trap: word-boundary
        matching alone isn't enough, because Bootstrap CSS class names are
        hyphen-separated ("col-lg-6", "d-lg-none") and a hyphen counts as a
        word boundary — "lg" inside "col-lg-6" matches \\blg\\b even though
        it has nothing to do with the brand LG. A real Southwire cable page
        false-positived as "LG Electronics" this way. Two defenses: scan
        visible text (not raw markup, so CSS/class noise is gone), and never
        let a key this short/ambiguous be decided by a generic body scan —
        only trust it if the page's own title says so.
        """
        keys_by_specificity = sorted(KNOWN_BRANDS.keys(), key=len, reverse=True)

        def find_in(text: str, min_key_len: int = 0) -> Optional[tuple]:
            text_lower = text.lower()
            for keyword in keys_by_specificity:
                if len(keyword) < min_key_len:
                    continue
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    return KNOWN_BRANDS[keyword]
            return None

        # High precision: the page's own title/og:title/h1 almost always
        # names the actual brand — safe to trust even short keys here.
        soup = BeautifulSoup(html, "html.parser")
        for title_text in self._page_title_candidates(soup):
            match = find_in(title_text)
            if match:
                return match

        # Lower precision fallback: visible text only (never raw HTML/CSS),
        # and require a longer, less ambiguous key (skip 2-letter codes like
        # "lg"/"ge" here — too easy to false-positive even in real prose).
        visible_text = soup.get_text(separator=" ", strip=True)
        match = find_in(visible_text, min_key_len=3)
        if match:
            return match

        return None, None

    def _page_title_candidates(self, soup) -> list[str]:
        candidates = []
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            candidates.append(og_title["content"])
        if soup.title and soup.title.string:
            candidates.append(soup.title.string)
        h1 = soup.find("h1")
        if h1:
            candidates.append(h1.get_text(strip=True))
        return candidates

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

    def _extract_with_phrase(self, text: str) -> Optional[str]:
        """Extract 'With X' feature phrase (e.g. 'With CleanBoost™')."""
        patterns = [
            re.compile(r"With\s+([A-Z][A-Za-z\s™®]+?)(?:\s*,|\s*\.|$)", re.M),
            re.compile(r"featuring\s+([A-Z][A-Za-z\s™®]+?)(?:\s*,|\s*\.|$)", re.I),
        ]
        for pat in patterns:
            m = pat.search(text)
            if m:
                phrase = m.group(0).strip().rstrip(".,")
                if len(phrase) < 60:
                    return phrase
        return None

    def _extract_approvals(self, text: str) -> Optional[str]:
        """Extract standards and certifications (e.g. 'UL Listed|ENERGY STAR Certified')."""
        known = [
            "UL Listed", "cUL Listed", "ENERGY STAR Certified", "Energy Star",
            "NSF Certified", "CSA Certified", "ASSE 1006",
            "CEE Tier 2 Qualified", "CEE Tier 3 Qualified",
            "ADA Compliant", "DOE Compliant", "EPA Certified",
        ]
        found = [cert for cert in known if cert.lower() in text.lower()]
        return "|".join(found) if found else None

    def _find_pdf_links(self, soup, base_url: str) -> list[str]:
        """Find PDF spec sheet/manual links on a manufacturer page."""
        pdf_urls = []
        base_domain = base_url.split("/")[2] if "/" in base_url else ""
        
        pdf_keywords = ["spec", "sheet", "manual", "datasheet", "specification", "brochure", "product"]
        
        for tag in soup.find_all("a", href=True):
            href = tag["href"].lower()
            link_text = tag.get_text(strip=True).lower()
            
            # Must be a PDF link
            if not href.endswith(".pdf"):
                continue
            
            # Should be from same manufacturer domain or relative
            full_url = tag["href"]
            if full_url.startswith("/"):
                full_url = f"https://{base_domain}{full_url}"
            elif not full_url.startswith("http"):
                continue
            
            # Check if link text or href suggests it's a spec sheet
            if any(kw in href or kw in link_text for kw in pdf_keywords):
                pdf_urls.append(full_url)
            elif base_domain in full_url:
                pdf_urls.append(full_url)
        
        return pdf_urls
