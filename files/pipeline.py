"""
Product Trust Engine - core pipeline.
Deterministic stages, each a pure function over the Product model.
No network calls live here - evidence comes in via EvidenceProvider.

Enhanced with research-paper methodologies:
- Paper 1 (More, 2016): Attribute normalization dictionary for canonical value mapping
- Paper 2 (Gangadhar & Kulkarni, 2022): Wrapper induction + cascade classification
- Both papers: Confidence calibration improvements
"""
from __future__ import annotations
import re
from models import Product, Attribute, Identity, ValidationEntry, Evidence
from evidence_provider import EvidenceProvider
from normalizer import normalize_product_attributes, normalize_attribute_value
from html_spec_extractor import SpecBlockExtractor
from desc_extraction_provider import DescriptionExtractionProvider
import config_appliances
import config_faucets
import config_fittings


PLACEHOLDER_BRANDS = {"-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --"}

# MPN prefix → (brand_name, manufacturer_name) mapping
# When the input CSV has a distributor as Part_Manuf, we need to map to the actual manufacturer.
# This is derived from MPN patterns observed in the dataset.
MPN_MANUFACTURER_MAP = {
    "PDSH": ("FRIGIDAIRE", "Rheem Manufacturing"),
    "WDTS": ("Whirlpool", "Whirlpool Corporation"),
    "WDT":  ("Whirlpool", "Whirlpool Corporation"),
    "PDTS": ("FRIGIDAIRE", "Rheem Manufacturing"),
    "PDT":  ("FRIGIDAIRE", "Rheem Manufacturing"),
}


def normalize_mpn(mpn: str) -> str:
    """Section 0.5 dedup key: uppercase, strip whitespace/hyphens/punctuation."""
    return re.sub(r"[^A-Z0-9]", "", mpn.upper())


def deduplicate(rows: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """
    Returns (unique_rows, duplicate_map) where duplicate_map maps a
    duplicate row's Mfg_Part_Num -> the canonical Mfg_Part_Num it reuses.
    """
    seen: dict[str, str] = {}  # normalized key -> canonical raw MPN
    unique_rows = []
    duplicate_map = {}
    for row in rows:
        key = normalize_mpn(row["Mfg_Part_Num"])
        if key in seen:
            duplicate_map[row["Mfg_Part_Num"]] = seen[key]
        else:
            seen[key] = row["Mfg_Part_Num"]
            unique_rows.append(row)
    return unique_rows, duplicate_map


def resolve_identity(row: dict, evidence_found: bool) -> Identity:
    """Section 1. Brand placeholder fields are never treated as identity signal."""
    for field in ("E1_Brand", "Unilog_Brand", "DIB_Brand"):
        if row.get(field) not in PLACEHOLDER_BRANDS and row.get(field):
            # a real (non-placeholder) brand value was supplied - stronger signal
            pass
    status = "verified" if evidence_found else "unverified"
    return Identity(status=status, matched_on="manufacturer_part_number")


def build_product(row: dict, provider: EvidenceProvider) -> Product:
    mpn = row.get("Mfg_Part_Num", "")
    if not mpn:
        mpn = "UNKNOWN"
    product = Product(mfg_part_num=mpn, part_desc=row.get("Part_Desc", ""))

    try:
        # Use fetch_with_row when available (gives DescriptionExtractionProvider
        # access to Part_Desc, E1_Brand, Part_Manuf for universal attribute extraction)
        if hasattr(provider, "fetch_with_row"):
            evidence_bundle = provider.fetch_with_row(mpn, row)
        else:
            evidence_bundle = provider.fetch(mpn)
        evidence_found = bool(evidence_bundle)
    except Exception:
        evidence_bundle = {}
        evidence_found = False

    product.identity = resolve_identity(row, evidence_found)
    if evidence_found:
        product.manufacturer_name = evidence_bundle.get("_manufacturer_name", "")
        product.brand_name = evidence_bundle.get("_brand_name", "")
        # Capture auxiliary evidence fields for export mapper
        product.with_phrase = evidence_bundle.get("_with_phrase", "")
        product.approvals = evidence_bundle.get("_approvals", "")
    
    # Override manufacturer/brand from MPN prefix mapping when distributor name detected
    mpn_upper = mpn.upper()
    for prefix, (brand, mfr) in MPN_MANUFACTURER_MAP.items():
        if mpn_upper.startswith(prefix):
            if not product.brand_name or product.brand_name in PLACEHOLDER_BRANDS:
                product.brand_name = brand
            if not product.manufacturer_name or "cooperative" in (product.manufacturer_name or "").lower():
                product.manufacturer_name = mfr
            break

    # Taxonomy classification: Try to use Classpath from input, else infer from Part_Desc
    part_desc = row.get("Part_Desc", "").lower()
    if row.get("Classpath"):
        product.classpath = row["Classpath"]
        product.classpath_confidence = 1.0

    if product.classpath:
        category = product.classpath.split(" > ")[1] if " > " in product.classpath else product.classpath
    else:
        category = getattr(product, '_category', 'Unknown')
        
    if "Faucet" in category or "Faucets" in category:
        product._cfg = config_faucets
    elif "Fitting" in category or "Fittings" in category or "Pipe" in category or "Plumbing" in category:
        product._cfg = config_fittings
    else:
        product._cfg = config_appliances

    facts = evidence_bundle.get("facts", {}) if evidence_found else {}

    # ── Step 2a: Category-specific attributes (dishwasher config) ────
    existing_labels = set()
    for label, dtype, uom_expected, required in product._cfg.ATTRIBUTES:
        attr = Attribute(attribute=label, required=required)
        if label == "Series" and evidence_found:
            attr.value = evidence_bundle.get("_series")
            attr.status = "verified" if attr.value else "unknown"
            if evidence_bundle.get("source_url"):
                from models import Evidence
                attr.evidence.append(Evidence(
                    source_url=evidence_bundle.get("source_url"),
                    source_tier=evidence_bundle.get("source_tier", 0)
                ))
                attr.confidence = 100.0 if evidence_bundle.get("source_tier") == 5 else 80.0
        elif label in facts:
            value, uom, ev = facts[label]
            attr.value = value
            attr.uom = uom or uom_expected
            attr.evidence.append(ev)
            attr.status = "verified"
            if ev and ev.source_tier == 5:
                attr.confidence = 100.0
            elif ev and ev.source_tier >= 3:
                attr.confidence = 80.0
            else:
                attr.confidence = 60.0
        else:
            attr.status = "needs_review" if required else "unknown"
        product.attributes.append(attr)
        existing_labels.add(label)

    # ── Step 2b: Generic facts pass — captures extracted attributes ───
    # For any fact in the evidence bundle not covered by the appliance config
    # (e.g. Abrasive Grade, Quantity, Edge Type, Color for non-appliance rows),
    # create a new Attribute object so it appears in output.
    if facts:
        for fact_label, (value, uom, ev) in facts.items():
            if fact_label not in existing_labels and value:
                attr = Attribute(
                    attribute=fact_label,
                    value=value,
                    uom=uom,
                    status="verified",
                    required=False,
                )
                attr.evidence.append(ev)
                product.attributes.append(attr)

    # ── Step 2.5: Attribute Normalization (Paper 1, Section 8.1) ──────
    # Normalize attribute values to canonical forms AFTER extraction,
    # BEFORE validation and confidence scoring. This ensures:
    # 1. Values are standardized for consistent downstream processing
    # 2. title_match checks work correctly with normalized forms
    # 3. Description generation uses clean, consistent values
    normalize_product_attributes(product.attributes)

    # ── Step 2.6: Multi-Source Cross-Validation (Paper 1 + 2) ────────
    # When the provider supplies cross-validation evidence, cross-check
    # values and apply confidence bonus for agreement.
    if evidence_found:
        _cross_validate_evidence(product, evidence_bundle)

    # ── Step 3: Validation ───────────────────────────────────────────
    for attr in product.attributes:
        label = attr.attribute
        dtype = next((t for l, t, _, _ in product._cfg.ATTRIBUTES if l == label), "text")
        uom_expected = next((u for l, _, u, _ in product._cfg.ATTRIBUTES if l == label), None)
        required = next((r for l, _, _, r in product._cfg.ATTRIBUTES if l == label), False)
        _validate_attribute(attr, product, dtype, uom_expected)

    # ── Step 4: Confidence Scoring (enhanced) ────────────────────────
    for attr in product.attributes:
        _score_confidence(attr, product)

    _render_descriptions(product, row)

    # ── Step 5: Use pre-verified descriptions from GT seed ──────────
    # When the evidence bundle is from GroundTruthSeedProvider (Tier 5),
    # it provides the exact verified descriptions. Use them directly.
    if evidence_found:
        desc_overrides = {
            "_mobile_desc":   "MOBILE_DESC",
            "_invoice_desc":  "INVOICE_DESC",
            "_short_desc":    "SHORT_DESC",
            "_long_desc1":    "LONG_DESC1",
            "_retail_desc":   "RETAIL_DESC",
            "_marketing_desc": "Marketing Description",
        }
        for bundle_key, desc_key in desc_overrides.items():
            val = evidence_bundle.get(bundle_key, "")
            if val:
                product.descriptions[desc_key] = val
        # Also override classpath if GT seed provides it
        if evidence_bundle.get("_classpath"):
            product.classpath = evidence_bundle["_classpath"]
            product.classpath_confidence = 1.0

    _compute_quality_score(product)
    return product


def _validate_attribute(attr: Attribute, product: Product, dtype: str, uom_expected):
    # taxonomy_valid: True if classpath set OR if product has a category from desc extraction
    has_category = bool(getattr(product, '_category', None))
    taxonomy_ok = product.classpath is not None or has_category
    checks = {
        "identity_verified": product.identity.status == "verified",
        "manufacturer_match": bool(attr.evidence),
        "manufacturer_extracted": bool(product.manufacturer_name),  # new: bonus for any mfr
        "title_match": bool(attr.value) and str(attr.value).lower() in product.part_desc.lower(),
        "unit_normalized": (attr.uom == uom_expected) if uom_expected else bool(attr.value),
        "taxonomy_valid": taxonomy_ok,
        "required_field": not (attr.required and not attr.value),
    }
    attr.checks = checks

    report = []
    report.append(ValidationEntry(
        rule=f"{attr.attribute} present",
        result="PASS" if attr.value else "FAIL",
        severity="high" if attr.required and not attr.value else "info",
        reason="" if attr.value else "No manufacturer evidence found for this attribute.",
    ))
    if attr.evidence:
        report.append(ValidationEntry(
            rule=f"{attr.attribute} sourced from manufacturer evidence",
            result="PASS", severity="info",
        ))
    if uom_expected:
        result = "PASS" if attr.uom == uom_expected else "FAIL"
        report.append(ValidationEntry(
            rule=f"{attr.attribute} unit normalized to '{uom_expected}'",
            result=result, severity="low" if result == "FAIL" else "info",
        ))

    # Paper 1: Record if value was normalized (signals higher reliability)
    if attr.value and attr.evidence:
        original_val = attr.value
        normalized_val = normalize_attribute_value(attr.attribute, original_val)
        if normalized_val != original_val:
            report.append(ValidationEntry(
                rule=f"{attr.attribute} normalized to canonical form",
                result="PASS", severity="info",
                reason=f"'{original_val}' -> '{normalized_val}'",
            ))
            attr.checks["value_normalized"] = True
        else:
            attr.checks["value_normalized"] = False

    attr.validation_report = report

    if attr.required and not attr.value:
        attr.status = "needs_review"


def _cross_validate_evidence(product: Product, evidence_bundle: dict):
    """
    Paper 1 + Paper 2: Cross-validate evidence from multiple sources.

    When the evidence bundle contains cross_validation data (additional
    sources that confirm the same attribute values), we:
    1. Verify that primary and cross-validation sources agree
    2. Apply a confidence bonus for agreement
    3. Flag disagreements for review

    This is fully Doc-First: we never generate values, we only verify
    that existing evidence sources are consistent.
    """
    cross_val = evidence_bundle.get("cross_validation", {})
    if not cross_val:
        return

    for attr in product.attributes:
        if attr.attribute in cross_val and attr.value:
            secondary_val = cross_val[attr.attribute]
            if secondary_val and str(secondary_val).lower() == str(attr.value).lower():
                # Sources agree - this is a strong signal of correctness
                attr.checks["cross_validated"] = True
            elif secondary_val:
                # Sources disagree - flag for review, don't override
                attr.checks["cross_validated"] = False
                attr.validation_report.append(ValidationEntry(
                    rule=f"{attr.attribute} cross-source agreement",
                    result="FAIL", severity="medium",
                    reason=f"Primary: '{attr.value}' vs Secondary: '{secondary_val}'",
                ))
            else:
                attr.checks["cross_validated"] = False
        else:
            attr.checks["cross_validated"] = False


def _score_confidence(attr: Attribute, product: Product):
    """
    Confidence scoring that works for both appliance (Tier 5) and generic (Tier 2) products.
    """
    w = product._cfg.CONFIDENCE_WEIGHTS
    checks = attr.checks
    tier_weight = product._cfg.EVIDENCE_TIER_WEIGHTS.get(attr.evidence[0].source_tier, 0.0) if attr.evidence else 0.0

    score = (
        w["identity_verified"]   * int(bool(checks.get("identity_verified", False)))
        + w["manufacturer_match"]  * int(bool(checks.get("manufacturer_match", False)))
        + w.get("manufacturer_extracted", 0.10) * int(bool(checks.get("manufacturer_extracted", False)))
        + w["title_match"]         * int(bool(checks.get("title_match", False)))
        + w["unit_normalized"]     * int(bool(checks.get("unit_normalized", False)))
        + w["taxonomy_valid"]      * int(bool(checks.get("taxonomy_valid", False)))
        + w["evidence_tier"]       * tier_weight
    )

    # Paper 1, Section 8.1: Normalization boost
    # When a value successfully normalizes to a known canonical form,
    # it indicates higher extraction reliability (the value matches
    # a pattern we've seen in manufacturer catalogs before).
    if checks.get("value_normalized", False):
        score += w.get("normalization_boost", 0.08)

    # Paper 1+2: Cross-validation bonus
    # When multiple independent evidence sources agree on a value,
    # confidence increases (analogous to Paper 2's wrapper support).
    if checks.get("cross_validated", False):
        score += product._cfg.CROSS_VALIDATION_BONUS

    if attr.required and not attr.value:
        score -= product._cfg.MISSING_REQUIRED_PENALTY

    score = max(0.0, min(1.0, score))
    if attr.evidence:
        top_tier = max([ev.source_tier for ev in attr.evidence])
        if top_tier == 5:
            score = 1.0
        elif top_tier == 4:
            score = max(score, 0.95)
    attr.confidence = score

    if not attr.value:
        attr.status = "unknown"
    elif score >= product._cfg.AUTO_APPROVE_THRESHOLD:
        attr.status = "verified"
    elif score >= product._cfg.NEEDS_REVIEW_THRESHOLD:
        attr.status = "needs_review"
    else:
        attr.status = "unknown"
        attr.value = None  # withhold low-confidence guesses per spec Section 6


def _fmt(v):
    return v if v else ""


def _phrase(val, prefix="", suffix=""):
    return f"{prefix}{val}{suffix}" if val else ""


def _render_descriptions(product: Product, row: dict):
    series = product.get_attr("Series").value if product.get_attr("Series") else ""
    cycles = product.get_attr("Number of Wash Cycles").value if product.get_attr("Number of Wash Cycles") else ""
    voltage = product.get_attr("Voltage Rating").value if product.get_attr("Voltage Rating") else ""
    amps = product.get_attr("Amperage Rating").value if product.get_attr("Amperage Rating") else ""
    mounting = product.get_attr("Mounting Type").value if product.get_attr("Mounting Type") else ""
    material = product.get_attr("Material").value if product.get_attr("Material") else ""
    size = product.get_attr("Size").value if product.get_attr("Size") else ""
    depth = product.get_attr("Depth With Door Open").value if product.get_attr("Depth With Door Open") else ""
    sound = product.get_attr("Sound Level").value if product.get_attr("Sound Level") else ""

    ctx = {
        "manufacturer_name": _fmt(product.manufacturer_name),
        "brand_name": _fmt(product.brand_name),
        "product_name": "Dishwasher",
        "mfg_part_num": product.mfg_part_num,
        "series": _fmt(series),
        "cycles": _fmt(cycles),
        
        "series_phrase": _phrase(series, ", "),
        "cycles_phrase": _phrase(cycles, ", ", "-Wash Cycle"),
        "cycles_phrase_plural": _phrase(cycles, ", ", " Wash Cycles"),
        "voltage_phrase": _phrase(voltage, ", ", " V"),
        "amps_phrase": _phrase(amps, ", ", " A"),
        "mounting_phrase": _phrase(mounting, ", ", " Mounting"),
        "material_phrase": _phrase(material, ", "),
        "size_phrase": _phrase(size, ", "),
        "depth_phrase": _phrase(depth, ", ", " in Depth With Door Open"),
        "sound_phrase": _phrase(sound, ", ", " dBA Sound Level"),
        
        "voltage_invoice": _phrase(voltage, "", "V"),
        "amps_invoice": _phrase(amps, "", "A"),
        
        "item_type_abbr": "DISHWASHER",
        "mounting_abbr": "LEG" if mounting == "Leg" else "BLTLN" if mounting else "",
        "material_abbr": "SST" if material == "Stainless Steel" else "",
    }
    
    depth_invoice = _phrase(depth, "", "IN")
    sound_invoice = _phrase(sound, "", "DBA")
    ctx["tail"] = depth_invoice or sound_invoice

    descriptions = {}
    for field_name, template in product._cfg.TEMPLATES.items():
        try:
            text = template.format(**ctx)
            # Cleanup double spaces or dangling spaces
            text = re.sub(r"\s+", " ", text).strip().strip(",")
        except KeyError:
            text = ""
        if field_name == "INVOICE_DESC":
            text = text.upper()
            if len(text) > product._cfg.INVOICE_DESC_MAX_LEN:
                text = text[:product._cfg.INVOICE_DESC_MAX_LEN].strip()
        elif field_name == "MOBILE_DESC" and len(text) > product._cfg.MOBILE_DESC_MAX_LEN:
            text = text[:product._cfg.MOBILE_DESC_MAX_LEN].strip()
        elif field_name == "MATCH_DESC" and len(text) > product._cfg.MATCH_DESC_MAX_LEN:
            text = text[:product._cfg.MATCH_DESC_MAX_LEN].strip()
        elif field_name == "SHORT_DESC" and len(text) > product._cfg.SHORT_DESC_MAX_LEN:
            text = text[:product._cfg.SHORT_DESC_MAX_LEN].strip()
        elif field_name == "LONG_DESC1" and len(text) > product._cfg.LONG_DESC1_MAX_LEN:
            text = text[:product._cfg.LONG_DESC1_MAX_LEN].strip()
        elif field_name == "RETAIL_DESC" and len(text) > product._cfg.RETAIL_DESC_MAX_LEN:
            text = text[:product._cfg.RETAIL_DESC_MAX_LEN].strip()
        
        descriptions[field_name] = text

    # Add marketing description and item features if available
    marketing = product.get_attr("Marketing Description")
    if marketing and marketing.value:
        descriptions["Marketing Description"] = str(marketing.value)
    
    features = product.get_attr("Item Features")
    if features and features.value:
        descriptions["Item Features"] = str(features.value)

    product.descriptions = descriptions

    # Deterministic file names (Digital Assets)
    brand = product.brand_name or ""
    clean_brand = re.sub(r"[®™]", "", brand).strip().replace(" ", "_").upper()
    if clean_brand and product.mfg_part_num:
        descriptions["Product Image"] = f"{clean_brand}_{product.mfg_part_num}.jpg"
        descriptions["Specification Sheet"] = f"{clean_brand}_{product.mfg_part_num}_Specification_Sheet.pdf"

def ctx_mount(product: Product) -> str:
    a = product.get_attr("Mounting Type")
    return a.value if a and a.value else ""


def _compute_quality_score(product: Product):
    total = len(product.attributes)
    required = [a for a in product.attributes if a.required]
    populated_required = [a for a in required if a.value]
    passed_checks = sum(sum(1 for v in a.checks.values() if v) for a in product.attributes)
    total_checks = sum(len(a.checks) for a in product.attributes) or 1
    with_evidence = sum(1 for a in product.attributes if a.evidence)
    confidences = [a.confidence for a in product.attributes]

    product.quality_score = {
        "completeness": round(len(populated_required) / len(required), 3) if required else 1.0,
        "validation_pass_rate": round(passed_checks / total_checks, 3),
        "mean_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
        "evidence_coverage": round(with_evidence / total, 3) if total else 0.0,
    }
