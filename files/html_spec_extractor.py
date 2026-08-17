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
                            source_url="html_page",
                            source_tier=3,
                            page_or_section="specification block",
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
                    if len(raw_attr) > 60 or len(raw_val) > 200:
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
        """
        lower = raw_name.lower().strip()

        # Direct mapping to canonical labels
        mapping = {
            "voltage": "Voltage Rating",
            "voltage rating": "Voltage Rating",
            "amperage": "Amperage Rating",
            "amperage rating": "Amperage Rating",
            "amps": "Amperage Rating",
            "amp rating": "Amperage Rating",
            "sound level": "Sound Level",
            "decibel level": "Sound Level",
            "noise level": "Sound Level",
            "db": "Sound Level",
            "dba": "Sound Level",
            "material": "Material",
            "tub material": "Material",
            "finish": "Material",
            "mounting": "Mounting Type",
            "mounting type": "Mounting Type",
            "install type": "Mounting Type",
            "size": "Size",
            "dimensions": "Size",
            "product size": "Size",
            "height": "Minimum Height",
            "width": "Size",
            "depth": "Depth With Door Open",
            "depth with door open": "Depth With Door Open",
            "wash cycles": "Number of Wash Cycles",
            "number of wash cycles": "Number of Wash Cycles",
            "cycles": "Number of Wash Cycles",
            "cycle count": "Number of Wash Cycles",
            "series": "Series",
            "product series": "Series",
            "model": "Model",
            "model number": "Model",
            "mfg part num": "Model",
            "color": "Color",
            "colour": "Color",
            "plug type": "Plug Type",
            "power cord": "Plug Type",
            "additional information": "Additional Information",
            "features": "Additional Information",
        }

        return mapping.get(lower)

    def _detect_uom(self, value: str) -> Optional[str]:
        """Detect unit of measurement from a value string."""
        value_lower = value.lower()
        if re.search(r"\b\d+\s*v\b", value_lower):
            return "V"
        if re.search(r"\b\d+\s*a\b", value_lower):
            return "A"
        if re.search(r"\b\d+\s*dBA\b", value_lower) or re.search(r"\b\d+\s*db\b", value_lower):
            return "dBA"
        if re.search(r"\bin\b", value_lower) or re.search(r"inch", value_lower):
            return "in"
        return None
