"""
Category Configuration: Fittings (Pipe / Tube / Hose Fittings)
Matches Fittings_LOV.xlsx schema rules for the UniHack Hackathon.
"""

CLASSPATH = "Plumbing>Pipe and Tubing>Pipe Fittings"

# Section 3: Attribute list
ATTRIBUTES = [
    # (label, type, uom, required)
    ("Fitting Type", "enum", None, True),
    ("Connection Type 1", "enum", None, True),
    ("Connection Type 2", "enum", None, False),
    ("Connection Type 3", "enum", None, False),
    ("Material", "enum", None, True),
    ("Schedule", "enum", None, False),
    ("Maximum Pressure", "number", "psi", False),
    ("Maximum Temperature", "number", "F", False),
    ("Pipe Size", "text", "in", True),
    ("Wall Thickness", "number", "in", False),
    ("Length", "number", "in", False),
    ("Standards", "text", None, False),
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
    5: 1.0,   
    4: 0.9,   
    3: 0.75,  
    2: 0.5,   
    1: 0.35,  
    0: 0.0,   
}

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

TEMPLATES = {
    "INVOICE_DESC": "{fitting_type} {material_abbr} {pipe_size}",
    "MOBILE_DESC": "{manufacturer_name} {brand_name}, {fitting_type}, {mfg_part_num}",
    "MATCH_DESC": "{brand_name} {mfg_part_num} {fitting_type} {material}",
    "SHORT_DESC": "{brand_name} {mfg_part_num} {fitting_type}, {material}, {pipe_size}",
    "LONG_DESC1": "{brand_name} {fitting_type}, {material}, {pipe_size}, {connection_phrase}, {pressure_phrase}",
    "RETAIL_DESC": "{fitting_type}, {material}, {pipe_size}",
}

INVOICE_DESC_MAX_LEN = 40
MOBILE_DESC_MAX_LEN = 80
MATCH_DESC_MAX_LEN = 120
SHORT_DESC_MAX_LEN = 200
RETAIL_DESC_MAX_LEN = 500
LONG_DESC1_MAX_LEN = 800

APPROVED_UOM = {
    "in": "in",      
    "psi": "psi",    
    "F": "F",      
    "lb": "lb",      
    "oz": "oz",      
}

UOM_PATTERNS = [
    (r"(\d+(?:\.\d+)?)\s*(?:inches?|IN\.|in\.|inch)", "in"),
    (r"(\d+(?:\.\d+)?)\s*(?:psi|PSI|pounds per square inch)", "psi"),
    (r"(\d+(?:\.\d+)?)\s*(?:F|Fahrenheit|degrees F)", "F"),
]

VALID_VALUES = {
    "Fitting Type": {
        "Elbow",
        "Tee",
        "Coupling",
        "Union",
        "Reducer",
        "Bushing",
        "Cap",
        "Plug",
        "Nipple",
        "Cross",
        "Adapter",
    },
    "Material": {
        "Brass",
        "Stainless Steel",
        "Carbon Steel",
        "Copper",
        "PVC",
        "CPVC",
        "PEX",
        "Cast Iron",
        "Galvanized Steel",
        "Bronze",
    },
    "Schedule": {
        "Schedule 40",
        "Schedule 80",
        "Schedule 120",
        "Schedule 10",
        "Schedule 5",
    },
    "Connection Type 1": {
        "Threaded (NPT)",
        "Threaded (BSPT)",
        "Flanged",
        "Welded",
        "Sweat",
        "Push-to-Connect",
        "Compression",
        "Flare",
        "Solvent Weld",
        "Grooved",
    },
    "Connection Type 2": {
        "Threaded (NPT)",
        "Threaded (BSPT)",
        "Flanged",
        "Welded",
        "Sweat",
        "Push-to-Connect",
        "Compression",
        "Flare",
        "Solvent Weld",
        "Grooved",
    },
}
