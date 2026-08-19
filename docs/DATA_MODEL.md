**Version:** 3.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Locked
**Last Updated:** 2026-08-18

# Data Model

All objects are dataclasses defined in `files/models.py`. Products have `to_dict()` serialization methods.

---

## Identity
**Fields:**
- `status` (str): `"verified"` | `"unverified"`
- `matched_on` (str): default `"manufacturer_part_number"`

---

## Evidence
**Purpose:** Cryptographic and traceable proof of a fact's origin.

**Fields:**
- `source_url` (str): URL or file path
- `source_tier` (int): 0–5 numeric scale (see config Section 2)
- `page_or_section` (str): location within source
- `retrieved_at` (str): ISO timestamp (auto-generated)
- `content_checksum` (str): hash for integrity verification

---

## ValidationEntry
**Purpose:** Single pass/fail check in the decision log.

**Fields:**
- `rule` (str): validation rule name
- `result` (str): `"PASS"` | `"FAIL"` (uppercase)
- `severity` (str): `"info"` | `"low"` | `"medium"` | `"high"`
- `reason` (str): human-readable explanation

---

## HistoryEntry
**Purpose:** Tracks value changes over time for audit trail.

**Fields:**
- `value` (str): the value at this point
- `timestamp` (str): ISO timestamp
- `evidence_ref` (str): reference to supporting evidence
- `reason` (str): why this value was set

---

## Attribute
**Purpose:** Single factual property (e.g., Voltage, Mounting Type).

**Fields:**
- `attribute` (str): attribute name
- `value` (Optional[str]): extracted value
- `uom` (Optional[str]): unit of measure
- `status` (str): `"verified"` | `"needs_review"` | `"unknown"`
- `confidence` (float): 0.0–1.0 score
- `evidence` (list[Evidence]): traceable proof chain
- `checks` (dict[str, bool]): validation check results
- `validation_report` (list[ValidationEntry]): detailed validation entries
- `history` (list[HistoryEntry]): value change audit trail
- `required` (bool): whether required for compliance

**Methods:**
- `to_dict()`: serializes to JSON-compatible dict (rounds confidence to 3 decimals)

---

## Product
**Purpose:** Canonical aggregate root for a single SKU.

**Fields:**
- `mfg_part_num` (str): manufacturer part number (primary key)
- `part_desc` (str): original part description
- `identity` (Identity): verification status
- `manufacturer_name` (Optional[str]): resolved manufacturer
- `brand_name` (Optional[str]): resolved brand
- `classpath` (Optional[str]): category classification
- `classpath_confidence` (float): classification confidence
- `attributes` (list[Attribute]): all extracted attributes
- `quality_score` (dict): `{completeness, validation_pass_rate, mean_confidence, evidence_coverage}`
- `descriptions` (dict): generated descriptions `{type: text}`

**Methods:**
- `get_attr(name)`: lookup attribute by name, returns `Optional[Attribute]`
- `to_dict()`: full serialization including nested attributes

---

## CategoryConfiguration
**Purpose:** Schema definition for a product class.

**Defined in:** `files/config_appliances.py`
- `ATTRIBUTES` (list): 50 appliance attributes with expected UOM
- `APPROVED_UOM` (dict): canonical UOM per attribute
- `UOM_PATTERNS` (dict): regex patterns for UOM extraction
- `VALID_VALUES` (dict): constrained vocabulary per attribute
- `EVIDENCE_TIER_WEIGHTS` (dict): confidence weights per source tier
- `CONFIDENCE_WEIGHTS` (dict): multi-factor scoring weights
- `TEMPLATES` (dict): description generation templates
- `REQUIRED_FIELDS` (list): fields required for compliance
