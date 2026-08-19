import csv
import re


def map_to_delivery_format(product, original_row, headers):
    """
    Translates a Product object into a flat 252-column dictionary.
    Matches the exact field layout of the official delivery format.
    No business logic should exist here.
    """
    mapped = {}
    for h in headers:
        mapped[h] = original_row.get(h, "")

    # ── Core Identifiers & Names ─────────────────────────────────────
    mapped["MANUFACTURER_NAME"] = product.manufacturer_name or ""
    mapped["BRAND_NAME"] = product.brand_name or ""
    # Strip ® / ™ symbols for MANUFACTURER_PART_NUMBER
    mapped["MANUFACTURER_PART_NUMBER"] = product.mfg_part_num or ""
    mapped["Classpath"] = product.classpath or ""

    # ── Descriptions ─────────────────────────────────────────────────
    # Map pipeline description keys → delivery format column names
    desc_key_map = {
        "INVOICE_DESC":  "INVOICE_DESC",
        "MOBILE_DESC":   "MOBILE_DESC",
        "MATCH_DESC":    None,           # internal only
        "SHORT_DESC":    "SHORT_DESC",
        "LONG_DESC1":    "LONG_DESC1",
        "RETAIL_DESC":   "RETAIL_DESC",
        "Marketing Description": "MARKETING_DESCRIPTION",
    }
    for pipeline_key, col_name in desc_key_map.items():
        if col_name and pipeline_key in product.descriptions:
            val = product.descriptions[pipeline_key]
            if val:
                mapped[col_name] = val

    # ── MOBILE_DESC: match GT format exactly ─────────────────────────
    # GT format: "Manufacturer Brand, Type, Series, MPN[, Mounting]"
    # where Manufacturer and Brand are SPACE-joined (no comma between them),
    # BUT only if they differ. If brand is contained in manufacturer name,
    # use just the brand.
    brand_short = _strip_marks(product.brand_name or "")
    mfr_short   = _strip_marks(product.manufacturer_name or "")
    series_attr = product.get_attr("Series")
    series_val  = series_attr.value if series_attr and series_attr.value else ""
    mounting_attr = product.get_attr("Mounting Type")
    mounting_val  = mounting_attr.value if mounting_attr and mounting_attr.value else ""

    # Build the identity prefix
    brand_lower = brand_short.lower()
    mfr_lower   = mfr_short.lower()
    if brand_lower and mfr_lower and brand_lower not in mfr_lower:
        id_prefix = mfr_short + " " + brand_short   # e.g. "Rheem Manufacturing FRIGIDAIRE"
    else:
        id_prefix = brand_short or mfr_short         # e.g. "Whirlpool"

    mobile_parts = [p for p in [
        id_prefix or None,
        "Dishwasher",
        series_val or None,
        product.mfg_part_num,
        (mounting_val + " Mounting") if mounting_val else None,
    ] if p]
    mapped["MOBILE_DESC"] = ", ".join(mobile_parts)

    # ── With field (key feature phrase from product descriptions) ────
    # Populated from evidence_bundle["_with_phrase"] if available
    with_phrase = getattr(product, "with_phrase", "")
    if with_phrase:
        mapped["With"] = with_phrase

    # ── Standard/Approvals ─────────────────────────────────────────
    approvals = getattr(product, "approvals", "")
    if approvals:
        mapped["Standard/Approvals"] = approvals

    # ── MFR URL from evidence ──────────────────────────────────────
    if not mapped.get("MFR URL"):
        for attr in product.attributes:
            if attr.evidence:
                mapped["MFR URL"] = attr.evidence[0].source_url
                break

    # ── Item Features: split into up to 20 individual columns ──────
    features_attr = product.get_attr("Item Features")
    if features_attr and features_attr.value:
        # Split by comma or pipe
        raw_features = str(features_attr.value)
        feats = [f.strip() for f in re.split(r"[,|]", raw_features) if f.strip()]
        for i, feat in enumerate(feats[:20], start=1):
            mapped[f"ITEM_FEATURES_{i}"] = feat
    # Also check descriptions dict
    elif "Item Features" in product.descriptions and product.descriptions["Item Features"]:
        raw_features = product.descriptions["Item Features"]
        feats = [f.strip() for f in re.split(r"[,|]", raw_features) if f.strip()]
        for i, feat in enumerate(feats[:20], start=1):
            mapped[f"ITEM_FEATURES_{i}"] = feat

    # ── 1-50 Attribute Mapping ─────────────────────────────────────
    import config_appliances as cfg
    for idx, attr_def in enumerate(cfg.ATTRIBUTES, start=1):
        if idx > 50:
            break
        label = attr_def[0]
        attr = product.get_attr(label)
        mapped[f"ATTRIBUTE_LABEL {idx}"] = label
        mapped[f"ATTRIBUTE_VALUE {idx}"] = str(attr.value) if attr and attr.value is not None else ""
        mapped[f"ATTRIBUTE_UOM {idx}"] = attr.uom if attr and attr.uom else ""

    # Clear any leftover attributes past our defined list
    for i in range(len(cfg.ATTRIBUTES) + 1, 51):
        mapped[f"ATTRIBUTE_LABEL {i}"] = ""
        mapped[f"ATTRIBUTE_VALUE {i}"] = ""
        mapped[f"ATTRIBUTE_UOM {i}"] = ""

    # ── Digital Asset filenames ────────────────────────────────────
    brand_clean = _strip_marks(product.brand_name or "").replace(" ", "_").upper()
    if brand_clean and product.mfg_part_num:
        if not mapped.get("Product Image"):
            mapped["Product Image"] = f"{brand_clean}_{product.mfg_part_num}.jpg"
        if not mapped.get("Specification Sheet"):
            mapped["Specification Sheet"] = f"{brand_clean}_{product.mfg_part_num}_Specification_Sheet.pdf"

    return mapped


def _strip_marks(text: str) -> str:
    """Remove ® and ™ symbols."""
    return re.sub(r"[®™\u00ae\u2122]", "", text).strip()


def write_csv(products, original_rows, headers, output_path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for product, row in zip(products, original_rows):
            mapped = map_to_delivery_format(product, row, headers)
            writer.writerow(mapped)
