import re
from collections import Counter

BUCKETS = [
    "export_slot_alignment",   # correct data, wrong ATTRIBUTE_*_N position
    "formatting_symbol",       # ® / ™ / spacing / casing only
    "description_template",    # punctuation, word order, missing clause
    "deterministic_missing",   # derivable by pattern (filenames, URLs) - not built yet
    "taxonomy_mapping",        # Dept/Class/Fine style - needs a lookup table
    "retrieval_missing",       # genuinely absent - no evidence source has it
    "unsupported_feature",     # out of category-config scope (warranty, video, etc.)
]

def normalize(s: str) -> str:
    return re.sub(r"[®™\s]+", "", (s or "").lower())

def classify(field: str, expected: str, generated: str) -> str:
    exp, gen = (expected or "").strip(), (generated or "").strip()

    if gen.lower() == "missing" or not gen:
        unsupported_markers = (
            "image", "warranty", "video", "standard", "approvals",
            "part_number", "sku", "dept", "class", "fine", "product name",
        )
        if any(m in field.lower() for m in unsupported_markers):
            if any(m in field.lower() for m in ("dept", "class", "fine")):
                return "taxonomy_mapping"
            if "image" in field.lower() or "specification sheet" in field.lower():
                return "deterministic_missing"
            return "unsupported_feature"
        return "retrieval_missing"

    if normalize(exp) == normalize(gen):
        return "formatting_symbol"

    if re.match(r"ATTRIBUTE_(LABEL|VALUE|UOM)[_ ]?\d+", field, re.I):
        return "export_slot_alignment"

    if field.upper().endswith("_DESC") or "DESCRIPTION" in field.upper():
        return "description_template"

    return "retrieval_missing"
