"""
Gemini Evidence Provider — LLM-powered attribute extraction.

Uses Google Gemini to extract structured product attributes from:
1. The Part_Desc field (always available)
2. Web search context (when available)

This provider fills gaps that deterministic extraction misses:
- Product series, features, certifications
- Detailed specifications from manufacturer knowledge
- Category classification for unknown product types

Evidence tier: 4 (LLM-extracted, high confidence when consistent)
Source: Gemini model knowledge (trained on manufacturer data)

Caching: Results are persisted to gemini_cache.json between runs.
Second time processing the same MPNs takes milliseconds, not seconds.
"""
from __future__ import annotations
import json
import os
import re
import time
import logging
from typing import Optional

from evidence_provider import EvidenceProvider
from models import Evidence

log = logging.getLogger(__name__)

# Load API key from .env
_API_KEY = None
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                _API_KEY = line.split("=", 1)[1].strip()
                break

# Gemini model
MODEL = "gemini-3.5-flash"

# Cache file
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_cache.json")

# Source description for evidence tracking
GEMINI_SOURCE_URL = "gemini://google/gemini-3.5-flash"
GEMINI_SOURCE_TIER = 4

# Appliance attribute schema — what we want Gemini to extract
ATTRIBUTE_SCHEMA = """
For the given product, extract as many of these attributes as you can find or infer:
- Series (product line name)
- Number of Wash Cycles (integer)
- Voltage Rating (number, e.g. 120)
- Amperage Rating (number, e.g. 15)
- Mounting Type (Leg, Built-in, Freestanding, Countertop, etc.)
- Size (dimensions like "24 in W x 24-1/4 in D")
- Depth With Door Open (number like "50-1/4")
- Minimum Height (number or range)
- Maximum Height (number or range)
- Sound Level (number in dBA)
- Material (Stainless Steel, Porcelain, etc.)
- Color (White, Black, Stainless Steel, etc.)
- Plug Type
- Weight
- Energy Star (Yes/No)
- Additional Information (energy usage, special features, etc.)
- With (special features like "CleanBoost", "Steam Clean", etc.)
- Standard/Approvals (UL Listed, ENERGY STAR Certified, etc.)
- Product Name (short product type name like "Dishwasher")
"""

EXTRACTION_PROMPT = """You are a product data extraction engine. Extract structured attributes from the product information below.

Product MPN: {mpn}
Product Description: {desc}
Manufacturer: {manufacturer}
{web_context}

IMPORTANT CONTEXT:
- If "Manufacturer" above is a real, specific company name (not blank, not a generic distributor/reseller account), treat it as the authoritative manufacturer for this product. Do not replace it with a different, better-known brand unless the description explicitly contradicts it.
- Do not default to a large, well-known consumer brand (Frigidaire, Whirlpool, LG, Samsung, etc.) out of habit. This dataset spans many industries — abrasives, plumbing, electrical, lumber, hardware, tools — and most products are made by specialized industrial manufacturers, not consumer-electronics companies. Only name a specific brand/manufacturer if you have real, specific knowledge that it made this exact model, or the input data already tells you.
- "SS" in descriptions means "Stainless Steel"
- For dishwashers specifically, common attributes include: wash cycles (3-8), voltage (120V typical), amperage (10-15A), mounting (Built-in/Leg/Freestanding), sound level (38-55 dBA) — this does not apply to other product types.

{attribute_schema}

Return ONLY a valid JSON object with this exact structure:
{{
  "brand": "actual brand name if genuinely known, otherwise null — never a guessed placeholder",
  "manufacturer": "full manufacturer company name if genuinely known, otherwise null",
  "classpath": "category path (e.g. Appliances > Kitchen Appliances > Built-In Dishwashers)",
  "attributes": {{
    "Series": "product line or null",
    "Number of Wash Cycles": "integer or null",
    "Voltage Rating": "number or null",
    "Amperage Rating": "number or null",
    "Mounting Type": "Leg/Built-in/Freestanding/Countertop or null",
    "Size": "dimensions string or null",
    "Depth With Door Open": "number or null",
    "Minimum Height": "number or range or null",
    "Maximum Height": "number or range or null",
    "Sound Level": "number in dBA or null",
    "Material": "Stainless Steel/White/Black etc or null",
    "Color": "color or null",
    "Plug Type": "type or null",
    "Weight": "weight or null",
    "Energy Star": "Yes/No or null",
    "Additional Information": "energy usage, features, or null",
    "With": "special features like CleanBoost, Steam Clean or null",
    "Standard/Approvals": "certifications like UL Listed, ENERGY STAR Certified or null",
    "Product Name": "short product type like Dishwasher or null"
  }}
}}

Rules:
- Use your training knowledge about real, publicly documented specifications for this exact MPN/model
- If you do not have reliable knowledge of this specific model, leave the field null — do not guess or invent a plausible-sounding value
- Only include attributes you are confident about
- Return ONLY the JSON, no other text
"""


class GeminiEvidenceProvider(EvidenceProvider):
    """
    LLM-powered evidence provider using Google Gemini.

    Extracts structured product attributes from Part_Desc and
    web search context using Gemini's knowledge base.

    Falls back to empty dict if:
    - API key not configured
    - API call fails after retries
    - Response cannot be parsed

    Caching: Results are persisted to disk between runs.
    """

    def __init__(self):
        self._client = None
        self._enabled = bool(_API_KEY)
        self._cache = {}
        # Circuit breaker: once the key's quota is clearly exhausted (a 429
        # response), stop spending a retry-with-backoff on every single row.
        # At 1000 rows, retrying a quota that resets on a per-minute/per-day
        # window (not per-request) just burns wall-clock time for nothing.
        self._circuit_open_until = 0.0
        self._circuit_cooldown_seconds = 30.0
        if self._enabled:
            try:
                from google import genai
                self._client = genai.Client(api_key=_API_KEY)
                self._load_cache()
                log.info("Gemini evidence provider initialized")
            except Exception as e:
                log.warning(f"Gemini init failed: {e}")
                self._enabled = False

    def _load_cache(self):
        """Load persistent cache from disk."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                log.info(f"Loaded {len(self._cache)} cached MPNs from gemini cache")
            except Exception:
                self._cache = {}

    def _save_cache(self):
        """Persist cache to disk."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def fetch(self, mfg_part_num: str) -> dict:
        """Not used directly — requires row context via fetch_with_row."""
        return {}

    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        """Extract product attributes using Gemini with retry and caching."""
        if not self._enabled or not self._client:
            return {}

        # Check cache first
        if mfg_part_num in self._cache:
            log.info(f"Gemini cache hit for {mfg_part_num}")
            return self._cache[mfg_part_num]

        if time.time() < self._circuit_open_until:
            log.info(f"Gemini circuit open (quota exhausted) — skipping {mfg_part_num} without a network call")
            return {}

        mpn = row.get("Mfg_Part_Num", "")
        desc = row.get("Part_Desc", "")
        manufacturer = row.get("Part_Manuf", "")

        if not mpn or not desc:
            return {}

        # Build web context if available
        web_context = ""

        prompt = EXTRACTION_PROMPT.format(
            mpn=mpn,
            desc=desc,
            manufacturer=manufacturer,
            web_context=web_context,
            attribute_schema=ATTRIBUTE_SCHEMA,
        )

        # One attempt, one short retry for a genuinely transient failure. A
        # 429 usually means a per-minute/per-day quota, not a per-request
        # blip — a local retry-with-backoff can't fix that, so instead we
        # trip the circuit breaker above and let every subsequent row skip
        # straight past Gemini until the cooldown expires.
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                )
                text = response.text.strip()

                # Extract JSON from response (handle markdown code blocks)
                json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                elif not text.startswith("{"):
                    brace_start = text.find("{")
                    brace_end = text.rfind("}") + 1
                    if brace_start >= 0 and brace_end > brace_start:
                        text = text[brace_start:brace_end]

                data = json.loads(text)
                result = self._build_evidence_bundle(data, mpn, desc)

                # Cache the result
                self._cache[mfg_part_num] = result
                self._save_cache()

                return result

            except json.JSONDecodeError as e:
                log.warning(f"Gemini JSON parse failed for {mpn}: {e}")
                return {}
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    self._circuit_open_until = time.time() + self._circuit_cooldown_seconds
                    log.warning(f"Gemini quota exhausted (429) — opening circuit for {self._circuit_cooldown_seconds}s")
                    return {}
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    if attempt == 0:
                        time.sleep(1.5)
                        continue
                    return {}
                log.warning(f"Gemini extraction failed for {mpn}: {e}")
                return {}

        return {}

    def _build_evidence_bundle(self, data: dict, mpn: str, desc: str) -> dict:
        """Convert Gemini response to standard evidence bundle."""
        ev = Evidence(
            source_url=GEMINI_SOURCE_URL,
            source_tier=GEMINI_SOURCE_TIER,
            page_or_section="Gemini LLM extraction from Part_Desc",
        )

        facts = {}
        attributes = data.get("attributes", {})

        for label, value in attributes.items():
            if value and value != "null" and str(value).strip():
                # Split value and UOM where applicable
                parsed_value, parsed_uom = self._parse_value_uom(str(value).strip())
                facts[label] = (parsed_value, parsed_uom, ev)

        # Build return bundle
        brand = data.get("brand") or ""
        manufacturer = data.get("manufacturer") or ""
        classpath = data.get("classpath") or ""
        series = facts.get("Series", (None, None, None))[0] if "Series" in facts else ""
        with_phrase = facts.get("With", (None, None, None))[0] if "With" in facts else ""
        approvals = facts.get("Standard/Approvals", (None, None, None))[0] if "Standard/Approvals" in facts else ""
        product_name = facts.get("Product Name", (None, None, None))[0] if "Product Name" in facts else ""

        return {
            "_manufacturer_name": manufacturer,
            "_brand_name": brand,
            "_series": series or "",
            "_mfr_url": GEMINI_SOURCE_URL,
            "_with_phrase": with_phrase or "",
            "_approvals": approvals or "",
            "_classpath": classpath,
            "_product_name": product_name or "",
            "facts": facts,
        }

    def _parse_value_uom(self, value: str) -> tuple[str, Optional[str]]:
        """Try to split a value into (value, uom) pair."""
        # Common UOM patterns
        uom_patterns = [
            (r"^(\d+(?:\.\d+)?)\s*(V)$", "V"),
            (r"^(\d+(?:\.\d+)?)\s*(A)$", "A"),
            (r"^(\d+(?:\.\d+)?)\s*(dBA)$", "dBA"),
            (r"^(\d+(?:\.\d+)?)\s*(in)$", "in"),
            (r"^(\d+(?:\.\d+)?)\s*(W)$", "W"),
            (r"^(\d+(?:\.\d+)?)\s*(lb)$", "lb"),
        ]
        for pattern, uom in uom_patterns:
            m = re.match(pattern, value, re.I)
            if m:
                return m.group(1), uom
        return value, None
