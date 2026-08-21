"""
Description Extraction Provider — Doc-First extraction from Part_Desc.
"""
from __future__ import annotations
import re
from typing import Optional

from evidence_provider import EvidenceProvider
from models import Evidence
from activity_tracker import tracker


DESC_SOURCE_TIER = 2
PLACEHOLDER_BRANDS = {"-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --"}

CATEGORY_KEYWORDS = {
    "Abrasives & Sanding": [
        "sanding", "abrasive", "disc", "belt", "sandpaper", "grit", "abranet",
        "stikit", "cubitron", "hiolit", "abr", "sand paper",
    ],
    "Cutting & Grinding": [
        "cut-off", "cutoff", "cut off", "grinding", "grind", "metal cut",
        "steel demon", "speed demon", "circular saw", "reciprocating",
    ],
    "Decking & Railing": [
        "decking", "railing", "rail kit", "baluster", "balusters", "deck",
        "azek", "timbertech", "trex", "composite", "pvc deck",
    ],
    "Plumbing": [
        "faucet", "valve", "fitting", "pipe", "hose", "flange", "coupling",
        "tee", "elbow", "nipple", "reducer", "union", "trap",
    ],
    "Electrical": [
        "wire", "cable", "conduit", "breaker", "panel", "switch",
        "outlet", "receptacle", "junction", "connector", "relay",
    ],
    "Appliances": [
        "dishwasher", "refrigerator", "washer", "dryer", "oven", "range",
        "microwave", "freezer", "cooktop", "hood",
    ],
    "Hardware & Fasteners": [
        "screw", "bolt", "nut", "washer", "anchor", "nail", "rivet",
        "staple", "clamp", "hinge", "bracket", "hook",
    ],
    "Tools": [
        "drill", "saw", "wrench", "pliers", "hammer", "screwdriver",
        "bit", "blade", "chuck", "collet", "arbor",
    ],
}

DIM_PATTERNS = [
    (re.compile(r'(\d+/\d+)"?\s*[xX]\s*(\d+(?:\.\d+)?)\s*"', re.I), "Size", "in"),
    (re.compile(r'(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*"?', re.I), "Size", None),
    (re.compile(r'(\d+(?:[\'\/\d\s.]+)?)\s*[xX]\s*(\d+(?:\.[0-9]+)?)\s*"\s*[xX]\s*(\d+(?:/\d+)?)\s*"', re.I), "Size", "in"),
    (re.compile(r'\b(\d+(?:-\d+/\d+)?)\s*"\s*(?![xX])', re.I), "Size", "in"),
    (re.compile(r"\b(\d+)'\s*(?![xX])", re.I), "Length", "ft"),
    (re.compile(r"\b(\d+)[xX](\d+)-(\d+)'", re.I), "Size", "in"),
]

GRIT_PATTERNS = [
    re.compile(r'\bP(\d{2,3})\b', re.I),
    re.compile(r'\b(\d{2,3})\s*[-]?\s*[Gg]rit\b', re.I),
]

QTY_PATTERNS = [
    re.compile(r'\b(\d+)\s*(pc|pcs|piece|pieces|disc/box|disc|pack|count|ct|rolls?|sheets?|box)\b', re.I),
    re.compile(r'\b(\d+)\s*(?:per|\/)\s*(box|case|pack|carton)\b', re.I),
]

DIAMETER_PATTERN = re.compile(r'(?:dia|diameter)\s*[:\-]?\s*(\d+(?:[-\/\.]\d+)?)\s*(?:in\.?|inch|")?', re.I)
THICKNESS_PATTERN = re.compile(r'(?:thk|thickness)\s*[:\-]?\s*(\d+(?:[-\/\.]\d+)?)\s*(?:in\.?|inch|")?', re.I)
ARBOR_PATTERN = re.compile(r'(\d+/\d+)"?\s*(?:arbor|bore|hub)', re.I)
RPM_PATTERN = re.compile(r'(?:max\.?\s*)?(\d{4,6})\s*(?:rpm|R\.P\.M)', re.I)
WIRE_GAUGE_PATTERN = re.compile(r'\b(\d{1,2})\s*(?:awg|ga|gauge)\b', re.I)
CONDUCTORS_PATTERN = re.compile(r'\b(\d{1,2})/(\d)\s*(?:awg|gauge|uf|nm|thhn|cable|wire)\b', re.I)
THREAD_PATTERN = re.compile(r'#(\d+[-\.]\d+)', re.I)
HEAD_PATTERN = re.compile(r'\b(phil?lips|flat\s+head|hex\s+head|pan\s+head|round\s+head|bugle\s+head|countersunk|socket\s+head)\s*(?:head|screw)?\b', re.I)
DRIVE_PATTERN = re.compile(r'\b(phil?lips|torx|sq|square|slotted|pozi|hex|allen)\s*(?:drive|bit)?\s*(?:#?\d+)?\b', re.I)
WOOD_SPECIES_PATTERN = re.compile(r'\b(southern\s+yellow\s+pine|pressure[-\s]treated\s+pine|cedar|redwood|spruce|fir|pine|oak|maple|birch|poplar|hickory|hemlock|cypress)\b', re.I)
GRADE_PATTERN = re.compile(r'\b(#\d|select|premium|common|grade\s*\d|clear)\b', re.I)
TREATMENT_PATTERN = re.compile(r'\b(pressure[-\s]treated|pt\b|acq|mcq|ca[-\s]b|ucfa|ucfb|ucfc|ground\s+contact|above\s+ground)\b', re.I)
PIPE_SIZE_PATTERN = re.compile(r'\b(\d+/\d+|\d+(?:\.\d+)?)\s*(?:in\.?|inch|")\s*(?:npt|pipe|pt|male|female)\b', re.I)
FLOW_RATE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(?:gpm|gallons?\s*per\s*minute)', re.I)
MAX_PRESSURE_PATTERN = re.compile(r'(\d+)\s*(?:psi|p\.s\.i)', re.I)
NUM_HANDLES_PATTERN = re.compile(r'(\d+)\s*[\-]?\s*[Hh]andle', re.I)
VOLTAGE_PATTERN = re.compile(r'(\d{2,3}(?:/\d{2,3})?)\s*(?:v(?:olts?)?|volt)', re.I)
AMPERAGE_PATTERN = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:a(?:mps?)?|amp)\b', re.I)
WATTAGE_PATTERN = re.compile(r'\b(\d+)\s*(?:w(?:atts?)?)\b', re.I)

FITTING_TYPE_KEYWORDS = {
    "Elbow": ["elbow", "ell"],
    "Tee": [" tee ", " tees "],
    "Coupling": ["coupling", "coupl"],
    "Union": ["union"],
    "Reducer": ["reducer", "reducing"],
    "Nipple": ["nipple"],
    "Plug": ["plug"],
    "Cap": [" cap "],
    "Adapter": ["adapter", "adaptor"],
}

CONNECTION_KEYWORDS = {
    "NPT": ["npt"],
    "FPT": ["fpt"],
    "MPT": ["mpt"],
    "Solder": ["solder", "sweat"],
    "Push": ["push", "sharkbite", "push-fit"],
    "Threaded": ["threaded", "thread"],
    "Compression": ["compression"],
}

MATERIAL_KEYWORDS = {
    "Stainless Steel": ["stainless steel", "stainless", "sst"],
    "Steel": ["steel", "metal"],
    "Aluminum": ["aluminum", "aluminium", "alum", "alm"],
    "PVC": ["pvc", "vinyl"],
    "Composite": ["composite", "wood-plastic"],
    "Brass": ["brass"],
    "Copper": ["copper"],
    "Iron": ["cast iron", "iron"],
    "Carbide": ["carbide"],
    "Diamond": ["diamond"],
    "Ceramic": ["ceramic"],
    "Silicon Carbide": ["silicon carbide", "sic"],
    "Aluminum Oxide": ["aluminum oxide", "al oxide"],
    "Ceramic Alumina": ["ceramic alumina"],
    "Tungsten Carbide": ["tungsten carbide"],
    "Fiberglass": ["fiberglass", "glass reinforced"],
    "Rubber": ["rubber"],
    "Concrete": ["concrete", "cement"],
    "Stone": ["stone", "natural stone"],
}

COLOR_KEYWORDS = {
    "White": ["white", " wh "],
    "Black": ["black", " blk "],
    "Gray": ["gray", "grey"],
    "Brown": ["brown"],
    "Red": ["red "],
    "Blue": ["blue"],
    "Green": ["green"],
    "Yellow": [" yellow "],
    "Natural": ["natural", " nat "],
    "Mahogany": ["mahogany", " mh "],
    "English Walnut": ["english walnut", " ew "],
    "Weathered Teak": ["weathered teak", " wt "],
    "American Walnut": ["american walnut", " aw "],
    "Castle Gate": ["castle gate", " cg "],
    "French White Oak": ["french white oak", " fw "],
    "Coastline": ["coastline", " cs "],
}

MOUNTING_KEYWORDS = {
    "Horizontal": ["horiz", "horizontal"],
    "Stair": ["stair", "str "],
    "Flat": ["fl ", "flat"],
}

EDGE_KEYWORDS = {
    "Square Edge": ["sq edge", "sq edg", "square edge"],
    "Grooved": ["grooved", " grv"],
    "Rounded": [" round edge", "round edg", " rd ", " rnd"],
}

PROFILE_KEYWORDS = {
    "Grooved": ["grooved", "grv"],
    "Square": ["sq ", "square"],
    "Smooth": ["smooth"],
    "Tongue and Groove": ["tongue", "t&g", "tongue and groove"],
}


def _make_ev(source_desc: str = "") -> Evidence:
    return Evidence(
        source_url=f"part_desc-{source_desc}",
        source_tier=DESC_SOURCE_TIER,
        page_or_section="Part_Desc field extraction",
    )


def _clean_brand(raw: str) -> str:
    raw = raw.strip()
    if raw in PLACEHOLDER_BRANDS:
        return ""
    return re.sub(r'\s*\(\w+\)\s*$', '', raw).strip()


def _classify_category(desc_lower: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "General Hardware"


def _extract_dimensions(desc: str):
    results = []
    for pat, attr_label, uom in DIM_PATTERNS:
        m = pat.search(desc)
        if m:
            value = m.group(0).strip().rstrip('"\'')
            results.append((attr_label, value, uom))
            break
    return results


def _extract_grit(desc: str):
    for pat in GRIT_PATTERNS:
        m = pat.search(desc)
        if m:
            return m.group(0)
    return None


def _extract_quantity(desc: str):
    for pat in QTY_PATTERNS:
        m = pat.search(desc)
        if m:
            return m.group(1) + " " + m.group(2).rstrip("s").capitalize()
    return None


def _extract_single(pattern, desc: str):
    m = pattern.search(desc)
    return m.group(1).strip() if m and m.group(1) else None


def _extract_material(desc_lower: str):
    for material, keywords in MATERIAL_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return material
    return None


def _extract_color(desc_lower: str):
    for color, keywords in COLOR_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return color
    return None


def _extract_mounting(desc_lower: str):
    for mounting, keywords in MOUNTING_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return mounting
    return None


def _extract_edge_type(desc_lower: str):
    for edge, keywords in EDGE_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return edge
    return None


def _extract_keyword_match(keyword_map, desc_lower: str):
    for label, keywords in keyword_map.items():
        if any(kw in desc_lower for kw in keywords):
            return label
    return None


def _extract_series_from_desc(desc: str):
    patterns = [
        re.compile(r'(Professional\s+Series|Eco\s+Series|Premium\s+Series|Elite\s+Series|Ultra\s+Series)', re.I),
        re.compile(r'(Steel\s+Demon|Speed\s+Demon|Cubitron\s+II|CleanBoost)', re.I),
        re.compile(r'(Vintage\s+Azek|Landmark\s+Azek|Select\s+Classic|Select\s+Alm)', re.I),
    ]
    for pat in patterns:
        m = pat.search(desc)
        if m:
            return m.group(0).strip()
    return None


class DescriptionExtractionProvider(EvidenceProvider):

    def fetch_from_row(self, row: dict) -> dict:
        mpn   = row.get("Mfg_Part_Num", "")
        desc  = row.get("Part_Desc", "")
        manuf = _clean_brand(row.get("Part_Manuf", ""))
        brand = _clean_brand(row.get("E1_Brand", ""))
        if not brand:
            brand = _clean_brand(row.get("Unilog_Brand", ""))
        if not brand:
            brand = _clean_brand(row.get("DIB_Brand", ""))

        desc_lower = desc.lower()
        # Strip MPN from description to avoid false matches on MPN digits
        desc_clean = desc
        if mpn and mpn in desc:
            desc_clean = desc.replace(mpn, '', 1).strip(' -')
        desc_clean_lower = desc_clean.lower()
        ev = _make_ev(mpn)
        facts = {}

        category = _classify_category(desc_lower)
        tracker.emit(
            mpn=mpn, step="desc_extraction", provider="DescriptionExtractionProvider",
            action="classify", detail=f"Category: {category} \u2014 Brand: {brand or 'unknown'}",
            icon="extract", status="running",
        )

        for attr_label, value, uom in _extract_dimensions(desc_clean):
            if value and attr_label not in facts:
                facts[attr_label] = (value, uom, ev)

        grit = _extract_grit(desc_clean)
        if grit:
            facts["Abrasive Grade"] = (grit, None, ev)

        qty = _extract_quantity(desc_clean)
        if qty:
            facts["Quantity"] = (qty, None, ev)

        diameter = _extract_single(DIAMETER_PATTERN, desc_clean)
        if diameter:
            facts["Diameter"] = (diameter, "in", ev)

        thickness = _extract_single(THICKNESS_PATTERN, desc_clean)
        if thickness:
            facts["Thickness"] = (thickness, "in", ev)

        arbor = _extract_single(ARBOR_PATTERN, desc_clean)
        if arbor:
            facts["Arbor Size"] = (arbor, "in", ev)

        rpm = _extract_single(RPM_PATTERN, desc_clean)
        if rpm:
            facts["Max RPM"] = (rpm, "rpm", ev)

        material = _extract_material(desc_clean_lower)
        if material:
            facts["Material"] = (material, None, ev)

        wood = _extract_single(WOOD_SPECIES_PATTERN, desc_clean)
        if wood:
            facts["Wood Species"] = (wood, None, ev)

        color = _extract_color(desc_clean_lower)
        if color:
            facts["Color"] = (color, None, ev)

        mounting = _extract_mounting(desc_clean_lower)
        if mounting:
            facts["Mounting Type"] = (mounting, None, ev)

        edge = _extract_edge_type(desc_clean_lower)
        if edge:
            facts["Edge Type"] = (edge, None, ev)

        profile = _extract_keyword_match(PROFILE_KEYWORDS, desc_clean_lower)
        if profile:
            facts["Profile"] = (profile, None, ev)

        fitting = _extract_keyword_match(FITTING_TYPE_KEYWORDS, desc_clean_lower)
        if fitting:
            facts["Fitting Type"] = (fitting, None, ev)

        conn = _extract_keyword_match(CONNECTION_KEYWORDS, desc_clean_lower)
        if conn:
            facts["Connection Type"] = (conn, None, ev)

        pipe_size = _extract_single(PIPE_SIZE_PATTERN, desc_clean)
        if pipe_size:
            facts["Pipe Size"] = (pipe_size, "in", ev)

        flow = _extract_single(FLOW_RATE_PATTERN, desc_clean)
        if flow:
            facts["Flow Rate"] = (flow, "gpm", ev)

        pressure = _extract_single(MAX_PRESSURE_PATTERN, desc_clean)
        if pressure:
            facts["Maximum Pressure"] = (pressure, "psi", ev)

        handles = _extract_single(NUM_HANDLES_PATTERN, desc_clean)
        if handles:
            facts["Number of Handles"] = (handles, None, ev)

        voltage = _extract_single(VOLTAGE_PATTERN, desc_clean)
        if voltage:
            facts["Voltage Rating"] = (voltage, "V", ev)

        amps = _extract_single(AMPERAGE_PATTERN, desc_clean)
        if amps:
            facts["Amperage Rating"] = (amps, "A", ev)

        watts = _extract_single(WATTAGE_PATTERN, desc_clean)
        if watts:
            facts["Wattage"] = (watts, "W", ev)

        wire_gauge = _extract_single(WIRE_GAUGE_PATTERN, desc_clean)
        if wire_gauge:
            facts["Wire Gauge"] = (wire_gauge, "AWG", ev)

        cond_match = CONDUCTORS_PATTERN.search(desc_clean)
        if cond_match:
            facts["Number of Conductors"] = (cond_match.group(1), None, ev)

        thread = _extract_single(THREAD_PATTERN, desc_clean)
        if thread:
            facts["Thread Size"] = (thread, None, ev)

        head = _extract_single(HEAD_PATTERN, desc_clean)
        if head:
            facts["Head Type"] = (head, None, ev)

        drive = _extract_single(DRIVE_PATTERN, desc_clean)
        if drive:
            facts["Drive Type"] = (drive, None, ev)

        grade = _extract_single(GRADE_PATTERN, desc_clean)
        if grade:
            facts["Grade"] = (grade, None, ev)

        treatment = _extract_single(TREATMENT_PATTERN, desc_clean)
        if treatment:
            facts["Treatment"] = (treatment, None, ev)

        series = _extract_series_from_desc(desc_clean)

        product_name = desc_clean

        bundle = {
            "_manufacturer_name": manuf,
            "_brand_name": brand,
            "_series": series,
            "source_url": ev.source_url,
            "source_tier": DESC_SOURCE_TIER,
            "_category": category,
            "_product_name": product_name,
            "_mfr_url": f"part_desc-{mpn}",
            "_with_phrase": "",
            "_approvals": "",
            "_classpath": "",
            "_mobile_desc": "",
            "_invoice_desc": "",
            "_short_desc": "",
            "_long_desc1": "",
            "_retail_desc": "",
            "_marketing_desc": "",
            "facts": facts,
        }

        if manuf or brand or facts or series:
            fact_names = ", ".join(facts.keys()) if facts else "none"
            tracker.emit(
                mpn=mpn, step="desc_extraction", provider="DescriptionExtractionProvider",
                action="done", detail=f"Extracted: {fact_names}",
                icon="done", status="success",
            )
            return bundle
        tracker.emit(
            mpn=mpn, step="desc_extraction", provider="DescriptionExtractionProvider",
            action="empty", detail=f"No extractable attributes from Part_Desc for {mpn}",
            icon="arrow", status="skip",
        )
        return {}

    def fetch(self, mfg_part_num: str) -> dict:
        return {}
