"""
Category Configuration: Generic (fallback for unrecognized categories)
Covers: abrasives, tools, plumbing, electrical, decking, lumber, hardware, etc.
Provides 30+ attributes so non-appliance products get rich extraction.
"""

CLASSPATH = ""

# Attributes that apply to virtually any physical product, regardless of
# sub-category — always included.
BASE_ATTRIBUTES = [
    # (label, type, uom, required)
    ("Series", "text", None, False),
    ("Model", "text", None, False),
    ("Size", "text", "in", False),
    ("Weight", "number", "lb", False),
    ("Material", "enum", None, False),
    ("Color", "enum", None, False),
    ("Quantity", "number", None, False),
    ("Additional Information", "text", None, False),
    ("Warranty", "text", None, False),
    ("EAN/UPC", "text", None, False),
    ("Marketing Description", "text", None, False),
    ("Item Features", "text", None, False),
]

ABRASIVES_ATTRIBUTES = [
    ("Abrasive Grade", "text", None, False),
    ("Grit", "text", None, False),
    ("Diameter", "number", "in", False),
    ("Thickness", "number", "in", False),
    ("Arbor Size", "text", "in", False),
    ("Max RPM", "number", "rpm", False),
    ("Length", "number", "in", False),
    ("Width", "number", "in", False),
    ("Pack Quantity", "number", None, False),
]

TOOLS_ATTRIBUTES = [
    ("Diameter", "number", "in", False),
    ("Thickness", "number", "in", False),
    ("Arbor Size", "text", "in", False),
    ("Max RPM", "number", "rpm", False),
    ("Edge Type", "text", None, False),
]

PLUMBING_ATTRIBUTES = [
    ("Fitting Type", "text", None, False),
    ("Connection Type", "text", None, False),
    ("Pipe Size", "text", "in", False),
    ("Flow Rate", "number", "gpm", False),
    ("Maximum Pressure", "number", "psi", False),
    ("Number of Handles", "integer", None, False),
    ("Faucet Type", "text", None, False),
]

ELECTRICAL_ATTRIBUTES = [
    ("Voltage Rating", "number", "V", False),
    ("Amperage Rating", "number", "A", False),
    ("Wattage", "number", "W", False),
    ("Wire Gauge", "text", None, False),
    ("Number of Conductors", "integer", None, False),
]

LUMBER_ATTRIBUTES = [
    ("Nominal Size", "text", None, False),
    ("Actual Size", "text", None, False),
    ("Wood Species", "text", None, False),
    ("Grade", "text", None, False),
    ("Treatment", "text", None, False),
    ("Profile", "text", None, False),
    ("Length", "number", "in", False),
]

HARDWARE_ATTRIBUTES = [
    ("Thread Size", "text", None, False),
    ("Head Type", "text", None, False),
    ("Drive Type", "text", None, False),
    ("Length", "number", "in", False),
]

GENERAL_ATTRIBUTES = [
    ("Mounting Type", "enum", None, False),
    ("Finish", "text", None, False),
    ("Height", "number", "in", False),
    ("Width", "number", "in", False),
]

# Keyword -> attribute set. Checked in order; a description can match more
# than one (e.g. a tool bit is both Tools and Hardware-ish) so sets are
# unioned by label, not exclusive.
_SUBCATEGORY_KEYWORDS = [
    (ABRASIVES_ATTRIBUTES, (
        "sand", "abrasive", "grit", "disc", "belt", "cubitron", "stikit",
        "hiolit", "abranet", "sanding",
    )),
    (TOOLS_ATTRIBUTES, (
        "cut-off", "cutoff", "grinding wheel", "blade", "drill bit",
        "router bit", "saw blade", "wheel", "bit ",
    )),
    (PLUMBING_ATTRIBUTES, (
        "valve", "pipe", "coupling", "hose", "faucet", "nipple", "elbow", "tee",
    )),
    (ELECTRICAL_ATTRIBUTES, (
        "wire", "cable", "conduit", "conductor", "awg", "electrical",
    )),
    (LUMBER_ATTRIBUTES, (
        "decking", "deck board", "railing", "rail kit", "composite decking",
        "lumber", "trex", "azek", "board",
    )),
    (HARDWARE_ATTRIBUTES, (
        "screw", "bolt", "nail", "nut ", "washer", "anchor", "fastener",
    )),
]


def get_attributes_for_desc(part_desc: str) -> list:
    """Real, deterministic attribute-schema routing: only ask questions that
    are structurally relevant to the detected product type. A sanding belt
    has no Wire Gauge or Wood Species — showing those as "unknown" isn't
    honest reporting, it's asking irrelevant questions. Matching on the
    description text (not a fixed one-size-fits-all list) keeps every
    attribute we DO ask about a real, answerable question for this product.
    """
    desc_lower = (part_desc or "").lower()
    matched = []
    for attrs, keywords in _SUBCATEGORY_KEYWORDS:
        if any(kw in desc_lower for kw in keywords):
            matched.append(attrs)

    if not matched:
        matched = [GENERAL_ATTRIBUTES]

    seen_labels = set()
    result = list(BASE_ATTRIBUTES)
    seen_labels.update(label for label, *_ in result)
    for attrs in matched:
        for entry in attrs:
            label = entry[0]
            if label not in seen_labels:
                result.append(entry)
                seen_labels.add(label)
    return result


# Backwards-compatible default (used only if no description is available).
ATTRIBUTES = BASE_ATTRIBUTES + GENERAL_ATTRIBUTES

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
