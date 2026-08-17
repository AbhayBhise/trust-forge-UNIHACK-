**Version:** 2.0  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Locked  
**Last Updated:** 2026-08-17

# Data Model

All objects are immutable dataclasses defined in `models.py`.

## Product
**Purpose:** Canonical aggregate root for a single SKU.  
**Lifecycle:** Created during deduplication → enriched by pipeline → serialized for export.  
**Fields:**
- `mfg_part_num` (str): Manufacturer part number (primary key)
- `part_desc` (str): Original part description
- `manufacturer_name` (str): Resolved manufacturer
- `brand_name` (str): Resolved brand
- `classpath` (str): Category classification
- `attributes` (dict[str, Attribute]): All extracted attributes
- `description` (str): Generated marketing description
- `pipeline_journey` (list[dict]): Audit trail of pipeline steps

## Attribute
**Purpose:** Single factual property (e.g., Voltage, Mounting Type).  
**Lifecycle:** Instantiated from config → populated via EvidenceProvider → scored by confidence engine.  
**Fields:**
- `attribute` (str): Attribute name
- `value` (Optional[str]): Extracted value
- `uom` (Optional[str]): Unit of measure
- `status` (str): `verified` | `needs_review` | `missing`
- `confidence` (float): 0.0–1.0 score
- `required` (bool): Whether required for compliance
- `source` (str): Evidence source identifier
- `evidence` (list[Evidence]): Traceable proof chain
- `validation` (list[ValidationEntry]): Pass/fail checks

## Evidence
**Purpose:** Cryptographic and traceable proof of a fact's origin.  
**Fields:**
- `source_url` (str): URL or file path
- `source_tier` (str): `hardcoded` | `pdf` | `web`
- `page_or_section` (str): Location within source
- `retrieved_at` (str): ISO timestamp

## ValidationEntry
**Purpose:** Single pass/fail check in the decision log.  
**Fields:**
- `rule` (str): Validation rule name
- `result` (str): `pass` | `fail`
- `severity` (str): `error` | `warning`
- `reason` (str): Human-readable explanation

## CategoryConfiguration
**Purpose:** Schema definition for a product class (e.g., Built-In Dishwashers).  
**Static Config:** `config_appliances.py`
- `ATTRIBUTES` (dict): 50 appliance attributes with UOM standards
- `APPROVED_UOM` (dict): Canonical UOM per attribute
- `UOM_PATTERNS` (dict): Regex patterns for UOM extraction
- `VALID_VALUES` (dict): Constrained vocabulary per attribute
- `EVIDENCE_TIER_WEIGHTS` (dict): Confidence weights per source
- `CONFIDENCE_WEIGHTS` (dict): Multi-factor weights
- `TEMPLATES` (dict): Description generation templates
- `REQUIRED_FIELDS` (list): Fields required for compliance
