"""
Category Configuration: Generic (fallback for unrecognized categories)
Provides reasonable default attributes for products that don't match
a specific category config (faucets, fittings, appliances).
"""

CLASSPATH = ""

# Generic attributes that apply to most product types
ATTRIBUTES = [
    # (label, type, uom, required)
    ("Material", "enum", None, False),
    ("Color", "enum", None, False),
    ("Size", "text", "in", False),
    ("Weight", "number", "lb", False),
    ("Additional Information", "text", None, False),
    ("Warranty", "text", None, False),
    ("EAN/UPC", "text", None, False),
    ("Marketing Description", "text", None, False),
    ("Item Features", "text", None, False),
]

MOUNTING_TYPE_VALUES = set()

# Section 2: Evidence quality tiers
EVIDENCE_TIER_WEIGHTS = {
    5: 1.0,   # manufacturer spec/datasheet PDF
    4: 0.9,   # manufacturer owner's/install manual
    3: 0.75,  # manufacturer product page (HTML)
    2: 0.5,   # manufacturer marketing/brochure page
    1: 0.35,  # manufacturer FAQ/support page
    0: 0.0,   # non-manufacturer source - not usable as evidence
}

# Section 6: confidence formula weights
CONFIDENCE_WEIGHTS = {
    "identity_verified": 0.22,
    "manufacturer_match": 0.18,
    "title_match": 0.06,
    "unit_normalized": 0.14,
    "taxonomy_valid": 0.14,
    "evidence_tier": 0.18,
    "normalization_boost": 0.08,
}
MISSING_REQUIRED_PENALTY = 0.30
AUTO_APPROVE_THRESHOLD = 0.75
NEEDS_REVIEW_THRESHOLD = 0.40

CROSS_VALIDATION_BONUS = 0.10
MAX_EVIDENCE_SOURCES = 3

# Description templates — generic
TEMPLATES = {
    "INVOICE_DESC": "{brand_name} {product_name} {material_phrase}",
    "MOBILE_DESC": "{manufacturer_name} {brand_name}, {product_name}, {mfg_part_num}",
    "MATCH_DESC": "{brand_name} {mfg_part_num} {product_name}",
    "SHORT_DESC": "{brand_name} {mfg_part_num} {product_name}{material_phrase}",
    "LONG_DESC1": "{brand_name} {product_name}{material_phrase}{size_phrase}",
    "RETAIL_DESC": "{product_name}{material_phrase}",
}

INVOICE_DESC_MAX_LEN = 40
MOBILE_DESC_MAX_LEN = 80
MATCH_DESC_MAX_LEN = 120
SHORT_DESC_MAX_LEN = 200
RETAIL_DESC_MAX_LEN = 500
LONG_DESC1_MAX_LEN = 800

APPROVED_UOM = {
    "V": "V",
    "A": "A",
    "dBA": "dBA",
    "in": "in",
    "W": "W",
    "kW": "kW",
    "hp": "hp",
    "lb": "lb",
    "oz": "oz",
    "ft": "ft",
    "BTU": "BTU",
}

UOM_PATTERNS = [
    (r"(\d+)\s*(?:Volts?|VOLTAGE|voltage)", "V"),
    (r"(\d+)\s*(?:Amps?|Amperes?|AMPERAGE)", "A"),
    (r"(\d+)\s*(?:dBA|dB|decibels?)", "dBA"),
    (r"(\d+(?:\.\d+)?)\s*(?:inches?|IN\.|in\.|inch)", "in"),
    (r"(\d+)\s*(?:Watts?|watt)", "W"),
    (r"(\d+)\s*(?:lbs?\.?|pounds?)", "lb"),
]

VALID_VALUES = {
    "Material": {
        "Stainless Steel", "Plastic", "Porcelain", "Glass", "Aluminum",
        "Steel", "Copper", "Brass", "Cast Iron", "Ceramic", "Zinc",
        "PVC", "CPVC", "PEX", "Carbon Steel", "Galvanized Steel", "Bronze",
        "Wood", "Granite", "Quartz", "Marble",
    },
    "Color": {
        "White", "Black", "Stainless Steel", "Silver", "Gray", "Red",
        "Blue", "Green", "Brown", "Beige", "Bisque", "Platinum",
        "Graphite", "Matte Black", "Slate", "Black Stainless", "Custom Panel",
        "Chrome", "Brushed Nickel", "Oil Rubbed Bronze", "Polished Brass",
    },
}
