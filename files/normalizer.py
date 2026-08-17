"""
Attribute Value Normalizer
Based on methodology from "Attribute Extraction from Product Titles in eCommerce"
(More, WalmartLabs 2016) - Section 8.1 Normalization.

After evidence extraction, attribute values are mapped to canonical forms using
a normalization dictionary. This runs AFTER extraction and never generates new
values - it only standardizes what was already found by the evidence providers.

The normalization dictionary maps variations -> canonical form:
  "120V" -> "120"
  "stainless steel" -> "Stainless Steel"
  "Built In" -> "Built-in"
"""
from __future__ import annotations
import re
from typing import Optional

# Import UOM standards from config
try:
    from config_appliances import APPROVED_UOM, UOM_PATTERNS, VALID_VALUES
except ImportError:
    APPROVED_UOM = {"V": "V", "A": "A", "dBA": "dBA", "in": "in"}
    UOM_PATTERNS = []
    VALID_VALUES = {}


# ── Normalization dictionaries per attribute ──────────────────────────────
# Each dict maps a raw extracted variation -> canonical value.
# Populated from ground truth analysis + manufacturer catalog patterns.

NORMALIZATION_MAPS: dict[str, dict[str, str]] = {
    "Voltage Rating": {
        "120v": "120",
        "120 V": "120",
        "120V": "120",
        "240v": "240",
        "240 V": "240",
        "240V": "240",
        "120/240v": "120/240",
    },
    "Amperage Rating": {
        "15a": "15",
        "15 A": "15",
        "15A": "15",
        "10a": "10",
        "10 A": "10",
        "10A": "10",
        "12a": "12",
        "12 A": "12",
        "12A": "12",
    },
    "Sound Level": {
        "47dba": "47",
        "47 dBA": "47",
        "47dBA": "47",
        "41dba": "41",
        "41 dBA": "41",
        "41dBA": "41",
        "44dba": "44",
        "44 dBA": "44",
        "44dBA": "44",
    },
    "Mounting Type": {
        "built in": "Built-in",
        "built-in": "Built-in",
        "Built In": "Built-in",
        "leg": "Leg",
        "freestanding": "Freestanding",
        "Freestanding": "Freestanding",
        "countertop": "Countertop",
    },
    "Material": {
        "stainless steel": "Stainless Steel",
        "Stainless steel": "Stainless Steel",
        "stainless Steel": "Stainless Steel",
        "plastic": "Plastic",
        "Plastic": "Plastic",
        "porcelain": "Porcelain",
        "Porcelain": "Porcelain",
    },
    "Number of Wash Cycles": {
        "5 cycles": "5",
        "5 Cycles": "5",
        "6 cycles": "6",
        "6 Cycles": "6",
        "8 cycles": "8",
        "8 Cycles": "8",
    },
    "Series": {
        "eco series": "Eco Series",
        "Eco series": "Eco Series",
        "professional series": "Professional Series",
        "Professional series": "Professional Series",
    },
    "Color": {
        "white": "White",
        "black": "Black",
        "stainless": "Stainless Steel",
        "stainless steel": "Stainless Steel",
        "silver": "Silver",
    },
}


def normalize_attribute_value(attribute_label: str, raw_value: str) -> str:
    """
    Normalize an extracted attribute value to its canonical form.

    Per Paper 1 Section 8.1: normalization maps variations of a single
    attribute value to a unique canonical representation. This is a
    deterministic lookup - no inference, no generation.

    Returns the canonical value if found in the normalization dictionary,
    otherwise returns the original value with whitespace stripped.
    """
    if not raw_value:
        return raw_value

    stripped = raw_value.strip()

    # Look up in normalization map for this attribute
    norm_map = NORMALIZATION_MAPS.get(attribute_label, {})
    normalized = norm_map.get(stripped)
    if normalized:
        return normalized

    # Case-insensitive fallback
    lower_map = {k.lower(): v for k, v in norm_map.items()}
    normalized = lower_map.get(stripped.lower())
    if normalized:
        return normalized

    # Pattern-based normalization for numeric fields with embedded units
    # e.g., "120V" -> "120" for voltage fields
    if attribute_label in ("Voltage Rating", "Amperage Rating", "Sound Level"):
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*[VvAaDd]*$", stripped)
        if num_match:
            return num_match.group(1)

    return stripped


def normalize_size_value(raw_value: str) -> str:
    """
    Normalize size/dimension values to a consistent format.
    Ensures consistent ordering: H x W x D and consistent unit spacing.
    """
    if not raw_value:
        return raw_value

    # Pattern: "33-7/16 in H x 23-7/8 in W x 22-5/8 in D"
    # or "24 in W x 24-1/4 in D" (partial)
    # Normalize spacing around "in" and dimensions
    normalized = raw_value.strip()
    # Ensure consistent spacing: "N in H" not "Nin H"
    normalized = re.sub(r"(\d)(in|IN)", r"\1 in", normalized)
    # Ensure consistent spacing around "x"
    normalized = re.sub(r"\s*x\s*", " x ", normalized)
    return normalized


def normalize_product_attributes(product_attrs: list) -> list:
    """
    Apply normalization to all attributes of a product.
    Called AFTER evidence extraction, BEFORE confidence scoring.

    This is the main entry point that pipeline.py calls.
    Modifies attributes in-place and returns the list.

    Steps:
    1. Normalize value to canonical form (Paper 1 normalization dictionary)
    2. Enforce UOM standards (Solution Guide: "only permitted way to write a unit")
    3. Validate enum values against constrained vocabulary (Solution Guide: "values must come from LOV")
    """
    for attr in product_attrs:
        if attr.value and attr.status == "verified":
            # Step 1: Normalize value
            if attr.attribute == "Size":
                attr.value = normalize_size_value(attr.value)
            else:
                attr.value = normalize_attribute_value(attr.attribute, attr.value)

            # Step 2: Enforce UOM standards
            attr.uom = enforce_uom(attr.attribute, attr.value, attr.uom)

            # Step 3: Validate enum values
            if attr.attribute in VALID_VALUES:
                if attr.value not in VALID_VALUES[attr.attribute]:
                    # Value not in approved list - flag for review
                    attr.validation_report.append(
                        __import__("models").ValidationEntry(
                            rule=f"{attr.attribute} value in approved vocabulary",
                            result="FAIL",
                            severity="medium",
                            reason=f"'{attr.value}' not in approved values: {sorted(VALID_VALUES[attr.attribute])}",
                        )
                    )

    return product_attrs


def enforce_uom(attribute_label: str, value: str, current_uom: Optional[str]) -> Optional[str]:
    """
    Enforce approved UOM abbreviations per Solution Guide rules.

    Rule: "always keep a space between the number and the unit"
    Rule: "The only permitted way to write a unit anywhere in your output"

    Returns the approved UOM string, or the current UOM if no transformation needed.
    """
    if not value:
        return current_uom

    # Check if the value contains a non-standard UOM that needs conversion
    for pattern, approved_uom in UOM_PATTERNS:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return approved_uom

    # If current_uom is set, ensure it's in the approved list
    if current_uom and current_uom in APPROVED_UOM:
        return APPROVED_UOM[current_uom]

    return current_uom
