"""
Smart Column Detection - maps ANY CSV column name to our internal schema.

Handles:
- Different naming conventions (MPN, Part_Number, model_number, Mfg_Part_Num)
- Case variations (MPN, mpn, Mpn)
- Whitespace and special characters
- Multiple possible column names for same field
- Missing columns (returns None for unfound fields)
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher


# Internal schema fields we need
INTERNAL_FIELDS = {
    "mpn": "Mfg_Part_Num",
    "manufacturer": "Part_Manuf",
    "brand": "E1_Brand",
    "description": "Part_Desc",
    "unilog_brand": "Unilog_Brand",
    "dib_brand": "DIB_Brand",
    "classpath": "Classpath",
    "sku": "SKU",
}

# Patterns that match each field (ordered by specificity)
FIELD_PATTERNS = {
    "mpn": [
        r"mpn", r"mfg.?part.?num", r"manufacturer.?part.?num", r"part.?num",
        r"model.?num", r"model.?number", r"product.?num", r"item.?num",
        r"part.?number", r"mfr.?part", r"catalog.?num", r"sku.?num",
        r"product.?code", r"item.?code", r"part.?code", r"model$",
        r"mfg.?part", r"mfr.?num", r"mfr.?number",
    ],
    "manufacturer": [
        r"manufacturer", r"mfr", r"mfr.?name", r"mfg.?name", r"vendor",
        r"supplier", r"brand.?owner", r"company", r"maker",
        r"part.?manuf", r"mfg.?company", r"mfr.?company",
    ],
    "brand": [
        r"^brand$", r"brand.?name", r"e1.?brand", r"dib.?brand",
        r"unilog.?brand", r"product.?brand", r"item.?brand",
        r"brand.?code", r"manufacturer.?brand",
    ],
    "description": [
        r"desc", r"description", r"part.?desc", r"product.?desc",
        r"item.?desc", r"short.?desc", r"product.?name", r"item.?name",
        r"part.?name", r"product.?description", r"item.?description",
    ],
    "unilog_brand": [
        r"unilog.?brand", r"unilog.?name",
    ],
    "dib_brand": [
        r"dib.?brand", r"dib.?name",
    ],
    "classpath": [
        r"classpath", r"class.?path", r"category", r"taxonomy",
        r"class", r"fine", r"dept",
    ],
    "sku": [
        r"^sku$", r"sku.?num", r"sku.?number", r"stock.?num",
        r"our.?sku", r"customer.?sku",
    ],
}

# Alias normalization for known column names
EXACT_ALIASES = {
    "mfg_part_num": "mpn",
    "mfg part num": "mpn",
    "manufacturer part number": "mpn",
    "part_number": "mpn",
    "part number": "mpn",
    "model_number": "mpn",
    "model number": "mpn",
    "mpn": "mpn",
    "part_manuf": "manufacturer",
    "part manuf": "manufacturer",
    "part manufacturer": "manufacturer",
    "manufacturer": "manufacturer",
    "manufacturer_name": "manufacturer",
    "manufacturer name": "manufacturer",
    "mfr": "manufacturer",
    "mfr_name": "manufacturer",
    "mfg": "manufacturer",
    "vendor": "manufacturer",
    "supplier": "manufacturer",
    "e1_brand": "brand",
    "e1 brand": "brand",
    "unilog_brand": "unilog_brand",
    "unilog brand": "unilog_brand",
    "dib_brand": "dib_brand",
    "dib brand": "dib_brand",
    "brand": "brand",
    "brand_name": "brand",
    "brand name": "brand",
    "part_desc": "description",
    "part desc": "description",
    "description": "description",
    "product_description": "description",
    "product description": "description",
    "item_description": "description",
    "item description": "description",
    "short_description": "description",
    "short description": "description",
    "classpath": "classpath",
    "class": "classpath",
    "category": "classpath",
    "taxonomy": "classpath",
    "dept": "classpath",
    "fine": "classpath",
    "sku": "sku",
    "sku_number": "sku",
    "sku number": "sku",
}


def normalize_column_name(name: str) -> str:
    """Normalize a column name for matching."""
    if not name:
        return ""
    # Lowercase, strip whitespace, replace spaces/underscores with nothing
    normalized = name.lower().strip()
    normalized = re.sub(r"[\s_\-\.]+", "", normalized)
    return normalized


def match_pattern(column_name: str, patterns: list[str]) -> bool:
    """Check if column name matches any of the regex patterns."""
    normalized = normalize_column_name(column_name)
    for pattern in patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True
    return False


def calculate_similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def detect_columns(headers: list[str]) -> dict[str, str | None]:
    """
    Detect which internal field each CSV column maps to.
    
    Returns dict mapping internal field name to CSV column name.
    Example: {"mpn": "Mfg_Part_Num", "manufacturer": "Part_Manuf", ...}
    """
    detected = {field: None for field in INTERNAL_FIELDS.values()}
    
    # Pass 1: Exact alias matching (highest confidence)
    for header in headers:
        normalized = normalize_column_name(header)
        if normalized in EXACT_ALIASES:
            internal_field = EXACT_ALIASES[normalized]
            csv_column = INTERNAL_FIELDS[internal_field]
            if detected[csv_column] is None:
                detected[csv_column] = header
    
    # Pass 2: Pattern matching for unmatched columns
    for header in headers:
        # Skip if already matched
        already_matched = False
        for csv_col in detected.values():
            if csv_col == header:
                already_matched = True
                break
        if already_matched:
            continue
        
        # Try pattern matching
        for field_key, patterns in FIELD_PATTERNS.items():
            csv_column = INTERNAL_FIELDS[field_key]
            if detected[csv_column] is None and match_pattern(header, patterns):
                detected[csv_column] = header
                break
    
    # Pass 3: Fuzzy matching for remaining unmatched columns
    unmatched_headers = [h for h in headers if h not in detected.values()]
    unmatched_fields = [f for f in detected.values() if f is None]
    
    for header in unmatched_headers:
        if not unmatched_fields:
            break
        
        best_match = None
        best_score = 0.0
        
        normalized_header = normalize_column_name(header)
        
        for field_key, csv_column in INTERNAL_FIELDS.items():
            if detected[csv_column] is not None:
                continue
            
            # Calculate similarity with field name
            field_normalized = normalize_column_name(field_key)
            score = calculate_similarity(normalized_header, field_normalized)
            
            if score > best_score and score > 0.6:  # 60% similarity threshold
                best_score = score
                best_match = csv_column
        
        if best_match:
            detected[best_match] = header
            unmatched_fields.remove(best_match)
    
    return detected


def map_row(row: dict, column_map: dict[str, str | None]) -> dict[str, str]:
    """
    Map a CSV row to our internal schema using the detected column map.
    
    Returns dict with our internal field names as keys.
    Missing fields get empty string values.
    """
    mapped = {}
    for internal_field, csv_column in column_map.items():
        if csv_column and csv_column in row:
            value = row[csv_column]
            # Clean placeholder values
            if value in ("-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --", ""):
                mapped[internal_field] = ""
            else:
                mapped[internal_field] = value or ""
        else:
            mapped[internal_field] = ""
    return mapped


def detect_and_report(headers: list[str]) -> tuple[dict[str, str | None], list[str]]:
    """
    Detect columns and return mapping + warnings.
    
    Returns (column_map, warnings) where warnings describe any issues.
    """
    column_map = detect_columns(headers)
    warnings = []
    
    # Check for critical missing fields
    if not column_map.get("Mfg_Part_Num"):
        warnings.append("CRITICAL: No MPN/Part Number column detected. Processing may fail.")
    
    if not column_map.get("Part_Manuf"):
        warnings.append("WARNING: No manufacturer column detected. Evidence sourcing limited.")
    
    if not column_map.get("Part_Desc"):
        warnings.append("WARNING: No description column detected. Taxonomy classification limited.")
    
    # Report detected columns
    detected = {k: v for k, v in column_map.items() if v is not None}
    if detected:
        warnings.append(f"Detected columns: {detected}")
    
    return column_map, warnings
