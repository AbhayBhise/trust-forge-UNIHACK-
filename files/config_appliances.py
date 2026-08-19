"""
Category Configuration: Appliances (Built-In Dishwashers)
Matches Product-Trust-Engine-Appliances-CategoryConfig-v1.md Sections 2-6.

Adding a new category = adding a new config module like this one,
not editing pipeline.py.
"""

CLASSPATH = "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers"

# Section 3: Attribute list
ATTRIBUTES = [
    # (label, type, uom, required)
    ("Series", "text", None, False),
    ("Model", "text", None, False),
    ("Number of Wash Cycles", "integer", None, False),
    ("Voltage Rating", "number", "V", True),
    ("Amperage Rating", "number", "A", True),
    ("Mounting Type", "enum", None, True),
    ("Plug Type", "text", None, False),
    ("Size", "text", "in", False),
    ("Depth With Door Open", "number", "in", False),
    ("Minimum Height", "text", "in", False),
    ("Maximum Height", "text", "in", False),
    ("Sound Level", "number", "dBA", True),
    ("Material", "enum", None, True),
    ("Color", "enum", None, False),
    ("Additional Information", "text", None, False),
    ("Warranty", "text", None, False),
    ("EAN/UPC", "text", None, False),
    ("List Price", "number", "$", False),
    ("Packaging Length", "number", "in", False),
    ("Packaging Width", "number", "in", False),
    ("Packaging Height", "number", "in", False),
    ("Marketing Description", "text", None, False),
    ("Item Features", "text", None, False),
    ("Product Image URL", "text", None, False),
    ("Specification Sheet URL", "text", None, False),
]

MOUNTING_TYPE_VALUES = {"Leg", "Built-in"}

# Section 2: Evidence quality tiers
EVIDENCE_TIER_WEIGHTS = {
    5: 1.0,   # manufacturer spec/datasheet PDF
    4: 0.9,   # manufacturer owner's/install manual
    3: 0.75,  # manufacturer product page (HTML)
    2: 0.5,   # manufacturer marketing/brochure page
    1: 0.35,  # manufacturer FAQ/support page
    0: 0.0,   # non-manufacturer source - not usable as evidence
}

# Section 6: confidence formula weights (enhanced with research-paper insights)
# Original weights + normalization_boost (Paper 1) + cross_validation (Paper 2)
# Weights are rebalanced so total remains ~1.0 before penalty.
CONFIDENCE_WEIGHTS = {
    "identity_verified": 0.22,
    "manufacturer_match": 0.18,
    "title_match": 0.14,
    "unit_normalized": 0.14,
    "taxonomy_valid": 0.14,
    "evidence_tier": 0.10,
    "normalization_boost": 0.08,  # Paper 1: value matched known canonical form
}
MISSING_REQUIRED_PENALTY = 0.30
AUTO_APPROVE_THRESHOLD = 0.75
NEEDS_REVIEW_THRESHOLD = 0.40

# Paper 1 + 2: Cross-validation bonus when multiple sources agree
CROSS_VALIDATION_BONUS = 0.10
# Paper 1: Maximum number of evidence sources to consider for cross-validation
MAX_EVIDENCE_SOURCES = 3

# Section 4: description templates.
# {field} placeholders are resolved from the Product's attributes/facts.
TEMPLATES = {
    "INVOICE_DESC": "{item_type_abbr} {mounting_abbr} {cycles} {material_abbr} {voltage_invoice} {amps_invoice} {tail}",
    "MOBILE_DESC": "{manufacturer_name} {brand_name}, {product_name}{series_phrase}, {mfg_part_num}",
    "MATCH_DESC": "{brand_name} {series} {mfg_part_num} {product_name}",
    "SHORT_DESC": "{brand_name} {series} {mfg_part_num} {product_name}{mounting_phrase}{cycles_phrase}{material_phrase}",
    "LONG_DESC1": "{brand_name} {product_name}{series_phrase}{cycles_phrase_plural}{voltage_phrase}{amps_phrase}{mounting_phrase}{size_phrase}{depth_phrase}{sound_phrase}{material_phrase}",
    "RETAIL_DESC": "{series} {product_name}{mounting_phrase}{cycles_phrase}{material_phrase}",
}

INVOICE_DESC_MAX_LEN = 40
MOBILE_DESC_MAX_LEN = 80
MATCH_DESC_MAX_LEN = 120
SHORT_DESC_MAX_LEN = 200
RETAIL_DESC_MAX_LEN = 500
LONG_DESC1_MAX_LEN = 800

# ── UOM Standards (from Solution Guide: "always keep a space between number and unit") ──
# Only the approved abbreviations for appliance attributes.
# Source: Solution Guide Section 4 - "The only permitted way to write a unit anywhere in your output."
APPROVED_UOM = {
    "V": "V",        # Voltage (never "Volts", "voltage", "V.")
    "A": "A",        # Amperage (never "Amps", "Amperes", "A.")
    "dBA": "dBA",    # Sound level (never "dB", "decibels")
    "in": "in",      # Dimensions (never "inches", "IN.", "inch")
    "W": "W",        # Wattage
    "kW": "kW",      # Kilowatts
    "hp": "hp",      # Horsepower
    "lb": "lb",      # Weight (never "lbs", "pounds")
    "oz": "oz",      # Ounces
    "ft": "ft",      # Feet (never "'")
    "BTU": "BTU",    # British Thermal Units
}

# Pattern to detect number+UOM that needs normalization
UOM_PATTERNS = [
    (r"(\d+)\s*(?:Volts?|VOLTAGE|voltage)", "V"),
    (r"(\d+)\s*(?:Amps?|Amperes?|AMPERAGE)", "A"),
    (r"(\d+)\s*(?:dBA|dB|decibels?)", "dBA"),
    (r"(\d+(?:\.\d+)?)\s*(?:inches?|IN\.|in\.|inch)", "in"),
    (r"(\d+)\s*(?:Watts?|watt)", "W"),
    (r"(\d+)\s*(?:lbs?\.?|pounds?)", "lb"),
]

# ── Enum Valid Values (constrained vocabularies for appliance attributes) ──
# Per Solution Guide: "Attribute values must come from the LOV files... 
# A fluent description made of invented values scores zero."
VALID_VALUES = {
    "Mounting Type": {
        "Leg",
        "Built-in",
        "Freestanding",
        "Countertop",
        "Undercounter",
        "Slide-In",
        "Drop-In",
        "Wall Mount",
        "Panel-Ready",
        "Portable",
    },
    "Material": {
        "Stainless Steel",
        "Plastic",
        "Porcelain",
        "Glass",
        "Aluminum",
        "Steel",
        "Copper",
        "Brass",
        "Cast Iron",
        "Ceramic",
    },
    "Color": {
        "White",
        "Black",
        "Stainless Steel",
        "Silver",
        "Gray",
        "Red",
        "Blue",
        "Green",
        "Brown",
        "Beige",
        "Bisque",
        "Platinum",
        "Graphite",
        "Matte Black",
        "Slate",
        "Black Stainless",
        "Custom Panel",
    },
    "Series": {
        "Eco Series",
        "Professional Series",
        "Ultra Series",
        "Premium Series",
        "Standard Series",
    },
}
