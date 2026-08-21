"""
Category Configuration: Generic (fallback for unrecognized categories)
Covers: abrasives, tools, plumbing, electrical, decking, lumber, hardware, etc.
Provides 30+ attributes so non-appliance products get rich extraction.
"""

CLASSPATH = ""

# Generic attributes that apply to most product types
# Organized by domain so any product gets reasonable coverage
ATTRIBUTES = [
    # (label, type, uom, required)
    # ── Identity ──
    ("Series", "text", None, False),
    ("Model", "text", None, False),
    # ── Dimensions ──
    ("Size", "text", "in", False),
    ("Length", "number", "in", False),
    ("Width", "number", "in", False),
    ("Height", "number", "in", False),
    ("Weight", "number", "lb", False),
    # ── Material / Finish ──
    ("Material", "enum", None, False),
    ("Color", "enum", None, False),
    ("Finish", "text", None, False),
    # ── Abrasives / Sanding ──
    ("Abrasive Grade", "text", None, False),
    ("Grit", "text", None, False),
    ("Diameter", "number", "in", False),
    ("Thickness", "number", "in", False),
    ("Arbor Size", "text", "in", False),
    ("Max RPM", "number", "rpm", False),
    ("Pack Quantity", "number", None, False),
    # ── Plumbing / Fittings ──
    ("Fitting Type", "text", None, False),
    ("Connection Type", "text", None, False),
    ("Pipe Size", "text", "in", False),
    ("Flow Rate", "number", "gpm", False),
    ("Maximum Pressure", "number", "psi", False),
    ("Number of Handles", "integer", None, False),
    ("Faucet Type", "text", None, False),
    # ── Electrical ──
    ("Voltage Rating", "number", "V", False),
    ("Amperage Rating", "number", "A", False),
    ("Wattage", "number", "W", False),
    ("Wire Gauge", "text", None, False),
    ("Number of Conductors", "integer", None, False),
    # ── Mounting / Install ──
    ("Mounting Type", "enum", None, False),
    ("Edge Type", "text", None, False),
    # ── Lumber / Decking ──
    ("Nominal Size", "text", None, False),
    ("Actual Size", "text", None, False),
    ("Wood Species", "text", None, False),
    ("Grade", "text", None, False),
    ("Treatment", "text", None, False),
    ("Profile", "text", None, False),
    # ── Hardware / Fasteners ──
    ("Thread Size", "text", None, False),
    ("Head Type", "text", None, False),
    ("Drive Type", "text", None, False),
    ("Quantity", "number", None, False),
    # ── General ──
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
    "manufacturer_extracted": 0.10,
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
    "gpm": "gpm",
    "psi": "psi",
    "rpm": "rpm",
}

UOM_PATTERNS = [
    (r"(\d+)\s*(?:Volts?|VOLTAGE|voltage)", "V"),
    (r"(\d+)\s*(?:Amps?|Amperes?|AMPERAGE)", "A"),
    (r"(\d+)\s*(?:dBA|dB|decibels?)", "dBA"),
    (r"(\d+(?:\.\d+)?)\s*(?:inches?|IN\.|in\.|inch)", "in"),
    (r"(\d+)\s*(?:Watts?|watt)", "W"),
    (r"(\d+)\s*(?:lbs?\.?|pounds?)", "lb"),
    (r"(\d+(?:\.\d+)?)\s*(?:gpm|GPM)", "gpm"),
    (r"(\d+)\s*(?:psi|PSI)", "psi"),
    (r"(\d+)\s*(?:rpm|RPM)", "rpm"),
]

VALID_VALUES = {
    "Material": {
        "Stainless Steel", "Plastic", "Porcelain", "Glass", "Aluminum",
        "Steel", "Copper", "Brass", "Cast Iron", "Ceramic", "Zinc",
        "PVC", "CPVC", "PEX", "Carbon Steel", "Galvanized Steel", "Bronze",
        "Wood", "Granite", "Quartz", "Marble", "Carbide", "Diamond",
        "Silicon Carbide", "Aluminum Oxide", "Ceramic Alumina",
        "Tungsten Carbide", "Composite", "Fiberglass", "Rubber",
    },
    "Color": {
        "White", "Black", "Stainless Steel", "Silver", "Gray", "Red",
        "Blue", "Green", "Brown", "Beige", "Bisque", "Platinum",
        "Graphite", "Matte Black", "Slate", "Black Stainless", "Custom Panel",
        "Chrome", "Brushed Nickel", "Oil Rubbed Bronze", "Polished Brass",
        "Natural", "Mahogany", "English Walnut", "Weathered Teak",
        "American Walnut", "Castle Gate", "French White Oak", "Coastline",
    },
}
