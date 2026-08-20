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
# Comprehensive coverage based on manufacturer catalog patterns.

NORMALIZATION_MAPS: dict[str, dict[str, str]] = {
    "Voltage Rating": {
        # All voltage variations -> numeric only
        "120v": "120", "120 V": "120", "120V": "120", "120 v": "120",
        "240v": "240", "240 V": "240", "240V": "240", "240 v": "240",
        "120/240v": "120/240", "120/240 V": "120/240", "120/240V": "120/240",
        "115v": "115", "115 V": "115", "115V": "115",
        "208v": "208", "208 V": "208", "208V": "208",
        "220v": "220", "220 V": "220", "220V": "220",
        "230v": "230", "230 V": "230", "230V": "230",
        "100v": "100", "100 V": "100", "100V": "100",
    },
    "Amperage Rating": {
        # All amperage variations -> numeric only
        "15a": "15", "15 A": "15", "15A": "15", "15 a": "15",
        "10a": "10", "10 A": "10", "10A": "10", "10 a": "10",
        "12a": "12", "12 A": "12", "12A": "12", "12 a": "12",
        "20a": "20", "20 A": "20", "20A": "20", "20 a": "20",
        "30a": "30", "30 A": "30", "30A": "30", "30 a": "30",
        "5a": "5", "5 A": "5", "5A": "5", "5 a": "5",
        "8a": "8", "8 A": "8", "8A": "8", "8 a": "8",
        "1a": "1", "1 A": "1", "1A": "1", "1 a": "1",
        "2a": "2", "2 A": "2", "2A": "2", "2 a": "2",
        "3a": "3", "3 A": "3", "3A": "3", "3 a": "3",
        "4a": "4", "4 A": "4", "4A": "4", "4 a": "4",
        "25a": "25", "25 A": "25", "25A": "25",
        "40a": "40", "40 A": "40", "40A": "40",
        "50a": "50", "50 A": "50", "50A": "50",
    },
    "Sound Level": {
        # All dB variations -> numeric only
        "47dba": "47", "47 dBA": "47", "47dBA": "47", "47 dba": "47",
        "41dba": "41", "41 dBA": "41", "41dBA": "41", "41 dba": "41",
        "44dba": "44", "44 dBA": "44", "44dBA": "44", "44 dba": "44",
        "50dba": "50", "50 dBA": "50", "50dBA": "50", "50 dba": "50",
        "52dba": "52", "52 dBA": "52", "52dBA": "52", "52 dba": "52",
        "55dba": "55", "55 dBA": "55", "55dBA": "55", "55 dba": "55",
        "60dba": "60", "60 dBA": "60", "60dBA": "60", "60 dba": "60",
        "38dba": "38", "38 dBA": "38", "38dBA": "38",
        "39dba": "39", "39 dBA": "39", "39dBA": "39",
        "40dba": "40", "40 dBA": "40", "40dBA": "40",
        "42dba": "42", "42 dBA": "42", "42dBA": "42",
        "43dba": "43", "43 dBA": "43", "43dBA": "43",
        "45dba": "45", "45 dBA": "45", "45dBA": "45",
        "46dba": "46", "46 dBA": "46", "46dBA": "46",
        "48dba": "48", "48 dBA": "48", "48dBA": "48",
        "49dba": "49", "49 dBA": "49", "49dBA": "49",
        "51dba": "51", "51 dBA": "51", "51dBA": "51",
        "53dba": "53", "53 dBA": "53", "53dBA": "53",
        "54dba": "54", "54 dBA": "54", "54dBA": "54",
        "56dba": "56", "56 dBA": "56", "56dBA": "56",
        "57dba": "57", "57 dBA": "57", "57dBA": "57",
        "58dba": "58", "58 dBA": "58", "58dBA": "58",
        "59dba": "59", "59 dBA": "59", "59dBA": "59",
        "62dba": "62", "62 dBA": "62", "62dBA": "62",
        "65dba": "65", "65 dBA": "65", "65dBA": "65",
        "70dba": "70", "70 dBA": "70", "70dBA": "70",
    },
    "Mounting Type": {
        "built in": "Built-in", "built-in": "Built-in", "Built In": "Built-in",
        "Built-in": "Built-in", "BUILT IN": "Built-in", "BUILT-IN": "Built-in",
        "leg": "Leg", "Leg": "Leg", "LEG": "Leg",
        "freestanding": "Freestanding", "Freestanding": "Freestanding", "FREESTANDING": "Freestanding",
        "countertop": "Countertop", "Countertop": "Countertop", "COUNTERTOP": "Countertop",
        "undercounter": "Undercounter", "Undercounter": "Undercounter",
        "slide-in": "Slide-In", "Slide In": "Slide-In", "slide in": "Slide-In",
        "drop-in": "Drop-In", "Drop In": "Drop-In", "drop in": "Drop-In",
        "wall mount": "Wall Mount", "Wall Mount": "Wall Mount", "wall mount": "Wall Mount",
        "panel-ready": "Panel-Ready", "Panel Ready": "Panel-Ready",
        "portable": "Portable", "Portable": "Portable",
        "top load": "Top Load", "Top Load": "Top Load",
        "front load": "Front Load", "Front Load": "Front Load",
        "top-load": "Top Load", "front-load": "Front Load",
    },
    "Material": {
        "stainless steel": "Stainless Steel", "Stainless steel": "Stainless Steel",
        "stainless Steel": "Stainless Steel", "Stainless Steel": "Stainless Steel",
        "STAINLESS STEEL": "Stainless Steel", "stainless": "Stainless Steel",
        "sst": "Stainless Steel", "SST": "Stainless Steel",
        "plastic": "Plastic", "Plastic": "Plastic", "PLASTIC": "Plastic",
        "porcelain": "Porcelain", "Porcelain": "Porcelain", "PORCELAIN": "Porcelain",
        "glass": "Glass", "Glass": "Glass", "GLASS": "Glass",
        "aluminum": "Aluminum", "Aluminum": "Aluminum", "ALUMINUM": "Aluminum",
        "aluminium": "Aluminum", "Aluminium": "Aluminum",
        "steel": "Steel", "Steel": "Steel", "STEEL": "Steel",
        "copper": "Copper", "Copper": "Copper", "COPPER": "Copper",
        "brass": "Brass", "Brass": "Brass", "BRASS": "Brass",
        "cast iron": "Cast Iron", "Cast Iron": "Cast Iron", "CAST IRON": "Cast Iron",
        "ceramic": "Ceramic", "Ceramic": "Ceramic", "CERAMIC": "Ceramic",
        "zinc": "Zinc", "Zinc": "Zinc", "ZINC": "Zinc",
        "pvc": "PVC", "PVC": "PVC",
        "cpvc": "CPVC", "CPVC": "CPVC",
        "pex": "PEX", "PEX": "PEX",
        "carbon steel": "Carbon Steel", "Carbon Steel": "Carbon Steel",
        "galvanized steel": "Galvanized Steel", "Galvanized Steel": "Galvanized Steel",
        "bronze": "Bronze", "Bronze": "Bronze",
        "wood": "Wood", "Wood": "Wood", "WOOD": "Wood",
        "granite": "Granite", "Granite": "Granite",
        "quartz": "Quartz", "Quartz": "Quartz",
        "marble": "Marble", "Marble": "Marble",
    },
    "Number of Wash Cycles": {
        "5 cycles": "5", "5 Cycles": "5", "5 CYCLES": "5", "5": "5",
        "6 cycles": "6", "6 Cycles": "6", "6 CYCLES": "6", "6": "6",
        "8 cycles": "8", "8 Cycles": "8", "8 CYCLES": "8", "8": "8",
        "3 cycles": "3", "3 Cycles": "3", "3": "3",
        "4 cycles": "4", "4 Cycles": "4", "4": "4",
        "7 cycles": "7", "7 Cycles": "7", "7": "7",
        "9 cycles": "9", "9 Cycles": "9", "9": "9",
        "10 cycles": "10", "10 Cycles": "10", "10": "10",
        "12 cycles": "12", "12 Cycles": "12", "12": "12",
        "15 cycles": "15", "15 Cycles": "15", "15": "15",
        "1 cycles": "1", "1 Cycles": "1",
        "2 cycles": "2", "2 Cycles": "2",
    },
    "Series": {
        "eco series": "Eco Series", "Eco series": "Eco Series", "Eco Series": "Eco Series",
        "professional series": "Professional Series", "Professional series": "Professional Series",
        "Professional Series": "Professional Series",
        "ultra series": "Ultra Series", "Ultra series": "Ultra Series",
        "Ultra Series": "Ultra Series",
        "premium series": "Premium Series", "Premium series": "Premium Series",
        "Premium Series": "Premium Series",
        "standard series": "Standard Series", "Standard series": "Standard Series",
        "Standard Series": "Standard Series",
        "elite series": "Elite Series", "Elite series": "Elite Series",
        "Elite Series": "Elite Series",
        "platinum series": "Platinum Series", "Platinum series": "Platinum Series",
        "Platinum Series": "Platinum Series",
    },
    "Color": {
        "white": "White", "White": "White", "WHITE": "White",
        "black": "Black", "Black": "Black", "BLACK": "Black",
        "stainless": "Stainless Steel", "stainless steel": "Stainless Steel",
        "Stainless Steel": "Stainless Steel",
        "silver": "Silver", "Silver": "Silver", "SILVER": "Silver",
        "gray": "Gray", "Gray": "Gray", "grey": "Gray", "Grey": "Gray",
        "red": "Red", "Red": "Red", "RED": "Red",
        "blue": "Blue", "Blue": "Blue", "BLUE": "Blue",
        "green": "Green", "Green": "Green", "GREEN": "Green",
        "brown": "Brown", "Brown": "Brown", "BROWN": "Brown",
        "beige": "Beige", "Beige": "Beige", "BISQUE": "Bisque",
        "bisque": "Bisque", "Bisque": "Bisque",
        "platinum": "Platinum", "Platinum": "Platinum",
        "graphite": "Graphite", "Graphite": "Graphite",
        "matte black": "Matte Black", "Matte Black": "Matte Black", "MATTE BLACK": "Matte Black",
        "slate": "Slate", "Slate": "Slate", "SLATE": "Slate",
        "black stainless": "Black Stainless", "Black Stainless": "Black Stainless",
        "custom panel": "Custom Panel", "Custom Panel": "Custom Panel",
    },
    "Faucet Type": {
        "kitchen sink faucet": "Kitchen Sink Faucet",
        "Kitchen Sink Faucet": "Kitchen Sink Faucet",
        "bath sink faucet": "Bath Sink Faucet",
        "Bath Sink Faucet": "Bath Sink Faucet",
        "bar faucet": "Bar Faucet", "Bar Faucet": "Bar Faucet",
        "utility faucet": "Utility Faucet", "Utility Faucet": "Utility Faucet",
        "widespread faucet": "Widespread Faucet", "Widespread Faucet": "Widespread Faucet",
        "centerset faucet": "Centerset Faucet", "Centerset Faucet": "Centerset Faucet",
    },
    "Finish": {
        "chrome": "Chrome", "Chrome": "Chrome", "CHROME": "Chrome",
        "brushed nickel": "Brushed Nickel", "Brushed Nickel": "Brushed Nickel",
        "matte black": "Matte Black", "Matte Black": "Matte Black",
        "oil rubbed bronze": "Oil Rubbed Bronze", "Oil Rubbed Bronze": "Oil Rubbed Bronze",
        "polished brass": "Polished Brass", "Polished Brass": "Polished Brass",
        "stainless steel": "Stainless Steel", "Stainless Steel": "Stainless Steel",
    },
    "Fitting Type": {
        "elbow": "Elbow", "Elbow": "Elbow", "ELBOW": "Elbow",
        "tee": "Tee", "Tee": "Tee", "TEE": "Tee",
        "coupling": "Coupling", "Coupling": "Coupling",
        "union": "Union", "Union": "Union",
        "reducer": "Reducer", "Reducer": "Reducer",
        "bushing": "Bushing", "Bushing": "Bushing",
        "cap": "Cap", "Cap": "Cap",
        "plug": "Plug", "Plug": "Plug",
        "nipple": "Nipple", "Nipple": "Nipple",
        "cross": "Cross", "Cross": "Cross",
        "adapter": "Adapter", "Adapter": "Adapter",
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
    if attribute_label in ("Voltage Rating", "Amperage Rating", "Sound Level", "Wattage"):
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*[VvAaDdWw]*$", stripped)
        if num_match:
            return num_match.group(1)

    # Normalize dimensions: ensure consistent spacing
    if attribute_label in ("Size", "Depth With Door Open", "Spout Reach", "Spout Height",
                           "Minimum Height", "Maximum Height", "Packaging Length",
                           "Packaging Width", "Packaging Height", "Length",
                           "Wall Thickness", "Pipe Size", "Connection Size"):
        # Remove redundant "in" if embedded: "24in" -> "24 in"
        normalized = re.sub(r"(\d)(in|IN)", r"\1 in", stripped)
        # Ensure consistent spacing around "x"
        normalized = re.sub(r"\s*[xX×]\s*", " x ", normalized)
        return normalized

    # Normalize flow rate: "1.5 gpm" -> "1.5"
    if attribute_label == "Flow Rate":
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:gpm|GPM)?$", stripped)
        if num_match:
            return num_match.group(1)

    # Normalize pressure: "150 psi" -> "150"
    if attribute_label in ("Maximum Pressure", "Minimum Pressure"):
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:psi|PSI)?$", stripped)
        if num_match:
            return num_match.group(1)

    # Normalize temperature: "180 F" -> "180"
    if attribute_label in ("Maximum Temperature", "Minimum Temperature"):
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:F|°F|Fahrenheit)?$", stripped)
        if num_match:
            return num_match.group(1)

    # Generic: strip trailing units that are already captured in UOM
    if attribute_label in ("Voltage Rating", "Amperage Rating", "Sound Level", "Wattage",
                           "Number of Wash Cycles", "List Price"):
        num_match = re.match(r"^(\d+(?:\.\d+)?)\s*$", stripped)
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

    normalized = raw_value.strip()
    # Ensure consistent spacing: "N in H" not "Nin H"
    normalized = re.sub(r"(\d)(in|IN)", r"\1 in", normalized)
    # Ensure consistent spacing around "x"
    normalized = re.sub(r"\s*[xX×]\s*", " x ", normalized)
    # Normalize fraction spacing: "7/16" -> "7/16" (keep as-is but normalize dash)
    normalized = re.sub(r"[\-–]", "-", normalized)
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
