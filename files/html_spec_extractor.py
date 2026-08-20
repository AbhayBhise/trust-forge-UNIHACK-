"""
HTML Specification Block Extractor
Based on methodology from "Extraction of Product Specifications from the Web"
(Gangadhar & Kulkarni, CODS-COMAD 2022).

This module extracts attribute-value pairs from HTML product pages using
specification block detection and wrapper induction techniques.

Key concepts applied:
- Section 3.1: Specification block classification using structural features
  (text field count, alpha-numeric ratio, repeating patterns)
- Section 3.2: Wrapper induction using seed attributes to bootstrap
  attribute-value extraction from repeating HTML patterns
- Section 5.3: Observation that specification blocks have consistent
  tag patterns even across different HTML structures

The approach is Doc-First: we only extract values that are explicitly
present in the HTML. If no specification block is found, we return
empty evidence rather than guessing.
"""
from __future__ import annotations
import re
from typing import Optional
from html.parser import HTMLParser
from models import Evidence


class SpecBlockExtractor:
    """
    Extracts product specification attribute-value pairs from raw HTML.

    Uses a two-phase approach inspired by Paper 2:
    1. Block Detection: Identify specification blocks by structural features
       (repeating patterns, text density, alpha-numeric ratio)
    2. Wrapper Extraction: Use seed attribute names to bootstrap extraction
       of attribute-value pairs from detected blocks
    """

    # Seed attributes for bootstrapping (Paper 2, Section 3.2)
    # These are used to identify which blocks contain specifications
    SEED_ATTRIBUTES = {
        "voltage", "amperage", "watts", "power", "capacity", "size",
        "dimension", "height", "width", "depth", "weight", "material",
        "color", "colour", "finish", "sound", "decibel", "db", "dba",
        "cycle", "wash", "mount", "type", "model", "series", "brand",
        "energy", "rating", "efficiency", "noise", "level",
    }

    # Blacklist: HTML tags that should not be traversed (Paper 2, Algorithm 1)
    BLACKLIST_TAGS = {"script", "style", "noscript", "svg", "path", "meta", "link"}

    def __init__(self):
        self._spec_patterns = self._build_spec_patterns()

    def _build_spec_patterns(self) -> list[re.Pattern]:
        """
        Build regex patterns for common specification block structures.
        These handle various HTML structures beyond tables/lists
        (Paper 2 contribution - generalizing across HTML elements).
        """
        patterns = [
            # Pattern: <dt>Attribute</dt><dd>Value</dd> (definition lists)
            re.compile(
                r"<dt[^>]*>\s*(.+?)\s*</dt>\s*<dd[^>]*>\s*(.+?)\s*</dd>",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <th>Attribute</th><td>Value</td> (table headers)
            re.compile(
                r"<th[^>]*>\s*(.+?)\s*</th>\s*<td[^>]*>\s*(.+?)\s*</td>",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <span class="attr">Attribute</span><span class="val">Value</span>
            re.compile(
                r'<span[^>]*class="[^"]*attr[^"]*"[^>]*>\s*(.+?)\s*</span>\s*'
                r'<span[^>]*class="[^"]*val[^"]*"[^>]*>\s*(.+?)\s*</span>',
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <div class="spec-row"><div>Attribute</div><div>Value</div></div>
            re.compile(
                r'<div[^>]*class="[^"]*spec[^"]*row[^"]*"[^>]*>\s*'
                r'<div[^>]*>\s*(.+?)\s*</div>\s*<div[^>]*>\s*(.+?)\s*</div>',
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: Attribute: Value (colon-separated, common in spec blocks)
            re.compile(
                r"<(?:p|div|span|li)[^>]*>\s*([A-Z][A-Za-z\s/&-]+?):\s*(.+?)\s*</(?:p|div|span|li)>",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <strong>Attribute</strong> Value
            re.compile(
                r"<strong[^>]*>\s*(.+?)\s*</strong>\s*[:\-]?\s*(.+?)(?:<|$)",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <b>Attribute</b> Value
            re.compile(
                r"<b[^>]*>\s*(.+?)\s*</b>\s*[:\-]?\s*(.+?)(?:<|$)",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <li><strong>Attribute</strong>: Value</li> (common in spec lists)
            re.compile(
                r"<li[^>]*>\s*<(?:strong|b)[^>]*>\s*(.+?)\s*</(?:strong|b)>\s*[:\-]?\s*(.+?)\s*</li>",
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <div class="spec-label">Attribute</div><div class="spec-value">Value</div>
            re.compile(
                r'<div[^>]*class="[^"]*label[^"]*"[^>]*>\s*(.+?)\s*</div>\s*'
                r'<div[^>]*class="[^"]*value[^"]*"[^>]*>\s*(.+?)\s*</div>',
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: <td class="spec-name">Attribute</td><td class="spec-data">Value</td>
            re.compile(
                r'<td[^>]*class="[^"]*(?:name|label|header)[^"]*"[^>]*>\s*(.+?)\s*</td>\s*'
                r'<td[^>]*class="[^"]*(?:data|value|detail)[^"]*"[^>]*>\s*(.+?)\s*</td>',
                re.IGNORECASE | re.DOTALL,
            ),
            # Pattern: data-label="Attribute" > Value (responsive tables)
            re.compile(
                r'data-(?:label|attribute)[^>]*>\s*(.+?)\s*</(?:th|td|div|span)>\s*'
                r'<(?:td|div|span)[^>]*>\s*(.+?)\s*</(?:td|div|span)>',
                re.IGNORECASE | re.DOTALL,
            ),
        ]
        return patterns

    def _strip_tags(self, html: str) -> str:
        """Remove HTML tags and decode entities."""
        text = re.sub(r"<[^>]+>", " ", html)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&#x27;", "'").replace("&quot;", '"').replace("&#8217;", "'")
        text = re.sub(r"&#?\w+;", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _detect_spec_block(self, html_block: str) -> bool:
        """
        Detect whether an HTML block is a specification block.
        Uses structural features from Paper 2 Section 3.1.1:
        - Text field count and density
        - Alpha-numeric ratio
        - Presence of repeating patterns
        """
        text = self._strip_tags(html_block)
        if len(text) < 20:
            return False

        # Feature: alpha-numeric ratio (spec blocks are text-heavy)
        alpha_num = sum(c.isalnum() or c.isspace() for c in text)
        ratio = alpha_num / max(len(text), 1)
        if ratio < 0.7:
            return False

        # Feature: presence of colon-separated pairs (key: value)
        colon_pairs = len(re.findall(r"[A-Z][a-zA-Z\s]+:\s*\S", text))
        if colon_pairs < 2:
            return False

        # Feature: seed attribute presence
        text_lower = text.lower()
        seed_hits = sum(1 for s in self.SEED_ATTRIBUTES if s in text_lower)
        if seed_hits < 1:
            return False

        # Feature: repeating tag patterns (wrapper consistency, Paper 2 Section 3.2)
        tag_pattern = re.findall(r"<(\w+)[^>]*>", html_block)
        if tag_pattern:
            from collections import Counter
            tag_counts = Counter(tag_pattern)
            # A spec block has a dominant tag (e.g., many <tr>, <li>, <div>)
            max_count = max(tag_counts.values())
            if max_count >= 3:
                return True

        return colon_pairs >= 3

    def extract_pairs(self, html: str) -> dict[str, tuple[str, Optional[str], Evidence]]:
        """
        Extract attribute-value pairs from HTML using wrapper induction.

        Paper 2 Algorithm 2 approach:
        1. Find blocks containing seed attributes (MatchTag)
        2. Extract row-wise pairs using the dominant wrapper pattern
        3. Bootstrap: newly found attributes can serve as additional seeds

        Returns: {attribute_label: (value, uom, Evidence)}
        """
        if not html:
            return {}

        # Phase 1: Find candidate specification blocks by splitting on
        # major structural elements
        candidates = self._split_into_blocks(html)
        spec_blocks = [b for b in candidates if self._detect_spec_block(b)]

        if not spec_blocks:
            # Fallback: try extracting from the full HTML
            spec_blocks = [html]

        # Phase 2: Extract pairs from detected blocks
        extracted = {}
        for block in spec_blocks:
            pairs = self._extract_from_block(block)
            for attr, val, uom in pairs:
                if attr and val:
                    # Normalize attribute name
                    attr_label = self._normalize_attr_name(attr)
                    if attr_label:
                        ev = Evidence(
                            source_url="html_parse",
                            source_tier=5,
                            page_or_section="spec table"
                        )
                        extracted[attr_label] = (val, uom, ev)

        return extracted

    def _split_into_blocks(self, html: str) -> list[str]:
        """
        Split HTML into candidate blocks using major structural tags.
        Paper 2 Algorithm 1: specTraverse splits on DOM children.
        """
        blocks = []
        # Split on common container tags
        for tag in ("table", "dl", "ul", "ol", "div", "section", "article"):
            pattern = re.compile(
                rf"<{tag}[^>]*>(.+?)</{tag}>", re.IGNORECASE | re.DOTALL
            )
            for match in pattern.finditer(html):
                blocks.append(match.group(0))

        # If no structured blocks found, split on <br> or <hr> as last resort
        if not blocks:
            blocks = re.split(r"<(?:br|hr)\s*/?>", html, flags=re.IGNORECASE)
            blocks = [b for b in blocks if len(b.strip()) > 20]

        return blocks

    def _extract_from_block(self, block: str) -> list[tuple[str, str, Optional[str]]]:
        """
        Extract attribute-value pairs from a single specification block.
        Tries each pattern and collects matches.
        """
        pairs = []
        seen_attrs = set()

        for pattern in self._spec_patterns:
            for match in pattern.finditer(block):
                groups = match.groups()
                if len(groups) >= 2:
                    raw_attr = self._strip_tags(groups[0]).strip()
                    raw_val = self._strip_tags(groups[1]).strip()

                    # Skip if empty or too long (likely not a spec pair)
                    if not raw_attr or not raw_val:
                        continue
                    if len(raw_attr) > 80 or len(raw_val) > 300:
                        continue

                    # Skip navigation/menu items (not specs)
                    skip_words = ["home", "contact", "about", "login", "sign up",
                                  "cart", "menu", "search", "subscribe", "newsletter",
                                  "copyright", "terms", "privacy", "policy"]
                    attr_lower = raw_attr.lower()
                    if any(sw in attr_lower for sw in skip_words):
                        continue

                    # Skip if value looks like a URL or email
                    if raw_val.startswith("http") or "@" in raw_val:
                        continue

                    # Skip if it's a duplicate
                    attr_key = raw_attr.lower()
                    if attr_key in seen_attrs:
                        continue
                    seen_attrs.add(attr_key)

                    # Determine UOM from value
                    uom = self._detect_uom(raw_val)

                    pairs.append((raw_attr, raw_val, uom))

        return pairs

    def _normalize_attr_name(self, raw_name: str) -> Optional[str]:
        """
        Map raw HTML attribute names to our canonical attribute labels.
        Returns None if the attribute is not in our schema.
        Comprehensive mapping covering appliances, tools, plumbing, electrical.
        """
        lower = raw_name.lower().strip()

        # Direct mapping to canonical labels
        mapping = {
            # Electrical
            "voltage": "Voltage Rating", "voltage rating": "Voltage Rating",
            "voltage (v)": "Voltage Rating",
            "amperage": "Amperage Rating", "amperage rating": "Amperage Rating",
            "amps": "Amperage Rating", "amp rating": "Amperage Rating",
            "amperage (a)": "Amperage Rating", "current": "Amperage Rating",
            # Sound
            "sound level": "Sound Level", "decibel level": "Sound Level",
            "noise level": "Sound Level", "db": "Sound Level", "dba": "Sound Level",
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
        }

        return mapping.get(lower)

    def _detect_uom(self, value: str) -> Optional[str]:
        """Detect unit of measurement from a value string."""
        value_lower = value.lower()
        if re.search(r"\b\d+\s*v\b", value_lower) or "volt" in value_lower:
            return "V"
        if re.search(r"\b\d+\s*a\b", value_lower) or "amp" in value_lower:
            return "A"
        if re.search(r"\b\d+\s*dBA\b", value_lower) or re.search(r"\b\d+\s*db\b", value_lower):
            return "dBA"
        if re.search(r"\bin\b", value_lower) or re.search(r"inch", value_lower):
            return "in"
        if re.search(r"\b\d+\s*w\b", value_lower) or "watt" in value_lower:
            return "W"
        if re.search(r"\b\d+\s*lb", value_lower) or "pound" in value_lower:
            return "lb"
        if re.search(r"\b\d+\s*gpm\b", value_lower) or "gallon" in value_lower:
            return "gpm"
        if re.search(r"\b\d+\s*psi\b", value_lower):
            return "psi"
        if re.search(r"\b\d+\s*ft\b", value_lower) or "feet" in value_lower:
            return "ft"
        return None
