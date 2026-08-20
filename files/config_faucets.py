"""
Category Configuration: Faucets (Kitchen and Bath Sink Faucets)
Matches Faucets_LOV.xlsx schema rules for the UniHack Hackathon.
"""

CLASSPATH = "Plumbing>Faucets>Kitchen and Bath Sink Faucets"

# Section 3: Attribute list
ATTRIBUTES = [
    # (label, type, uom, required)
    ("Faucet Type", "enum", None, True),
    ("Mounting Type", "enum", None, True),
    ("Number of Handles", "integer", None, True),
    ("Handle Type", "enum", None, False),
    ("Spout Type", "enum", None, False),
    ("Spout Reach", "number", "in", False),
    ("Spout Height", "number", "in", False),
    ("Flow Rate", "number", "gpm", True),
    ("Material", "enum", None, True),
    ("Finish", "enum", None, False),
    ("Valve Type", "enum", None, False),
    ("Connection Size", "text", "in", False),
    ("ADA Compliant", "enum", None, False),
    ("Additional Information", "text", None, False),
    ("Warranty", "text", None, False),
    ("EAN/UPC", "text", None, False),
    ("List Price", "number", "$", False),
    ("Marketing Description", "text", None, False),
    ("Item Features", "text", None, False),
    ("Product Image URL", "text", None, False),
    ("Specification Sheet URL", "text", None, False),
]

# Section 2: Evidence quality tiers
EVIDENCE_TIER_WEIGHTS = {
    5: 1.0,   # manufacturer spec/datasheet PDF or GT Seed
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

# Section 4: description templates.
TEMPLATES = {
    "INVOICE_DESC": "{brand_name} {product_name} {finish_abbr} {flow_rate}",
    "MOBILE_DESC": "{manufacturer_name} {brand_name}, {product_name}, {mfg_part_num}",
    "MATCH_DESC": "{brand_name} {mfg_part_num} {product_name} {faucet_type}",
    "SHORT_DESC": "{brand_name} {mfg_part_num} {product_name}, {mounting_phrase}, {finish_phrase}",
    "LONG_DESC1": "{brand_name} {product_name}, {faucet_type}, {mounting_phrase}, {handles_phrase}, {flow_rate_phrase}, {finish_phrase}",
    "RETAIL_DESC": "{product_name}, {mounting_phrase}, {finish_phrase}",
}

INVOICE_DESC_MAX_LEN = 40
MOBILE_DESC_MAX_LEN = 80
MATCH_DESC_MAX_LEN = 120
SHORT_DESC_MAX_LEN = 200
RETAIL_DESC_MAX_LEN = 500
LONG_DESC1_MAX_LEN = 800

APPROVED_UOM = {
    "in": "in",      # Dimensions
    "gpm": "gpm",    # Flow Rate
    "psi": "psi",    # Pressure
    "lb": "lb",      # Weight
    "oz": "oz",      # Ounces
}

UOM_PATTERNS = [
    (r"(\d+(?:\.\d+)?)\s*(?:inches?|IN\.|in\.|inch)", "in"),
    (r"(\d+(?:\.\d+)?)\s*(?:gpm|gallons per minute|GPM)", "gpm"),
]

VALID_VALUES = {
    "Faucet Type": {
        "Kitchen Sink Faucet",
        "Bath Sink Faucet",
        "Bar Faucet",
        "Utility Faucet",
        "Widespread Faucet",
        "Centerset Faucet",
    },
    "Mounting Type": {
        "Deck Mount",
        "Wall Mount",
        "Single Hole",
        "3-Hole",
        "4-Hole",
    },
    "Material": {
        "Brass",
        "Stainless Steel",
        "Zinc",
        "Plastic",
        "Copper",
    },
    "Finish": {
        "Chrome",
        "Brushed Nickel",
        "Matte Black",
        "Oil Rubbed Bronze",
        "Polished Brass",
        "Stainless Steel",
    },
    "ADA Compliant": {
        "Yes",
        "No",
    },
}
