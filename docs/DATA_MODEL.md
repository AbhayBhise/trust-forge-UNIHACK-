**Version:** 1.0  
**Date:** 2026-08-14  
**Owner:** AI Pipeline  
**Status:** Locked  
**Reviewed By:** User  
**Last Updated:** 2026-08-14  

# Data Model

This document defines the core domain objects of the Product Trust Engine. All objects are immutable dataclasses defined in `models.py`.

## Product
**Purpose:** The canonical aggregate root for a single SKU.
**Lifecycle:** Created during deduplication, enriched by the pipeline, serialized for export.
**Relationships:** Contains 1 `Identity`, many `Attributes`, 1 `QualityScore` map.
**Fields:** `mfg_part_num`, `part_desc`, `manufacturer_name`, `brand_name`, `classpath`, etc.
**Validation Rules:** Must have a valid `mfg_part_num`.
**Serialization:** `to_dict()` outputs JSON-serializable primitives.

## Attribute
**Purpose:** Represents a single factual property (e.g., Voltage, Mounting Type).
**Lifecycle:** Instantiated from category config, populated via EvidenceProvider, scored by confidence engine.
**Relationships:** Belongs to 1 `Product`, contains many `Evidence` and `ValidationEntry` objects.
**Fields:** `attribute`, `value`, `uom`, `status`, `confidence`, `required`.
**Validation Rules:** If `required` is true, `status` cannot be "verified" without a `value`.

## Evidence
**Purpose:** Cryptographic and traceable proof of a fact's origin.
**Lifecycle:** Created by `EvidenceProvider` upon extraction, attached to `Attribute`.
**Relationships:** Belongs to 1 `Attribute`.
**Fields:** `source_url`, `source_tier`, `page_or_section`, `retrieved_at`.

## ValidationEntry
**Purpose:** A single pass/fail check in the decision log.
**Lifecycle:** Created by the validation engine during pipeline execution.
**Relationships:** Belongs to 1 `Attribute`.
**Fields:** `rule`, `result`, `severity`, `reason`.

## CategoryConfiguration
**Purpose:** Schema definition for a specific product class (e.g., Built-In Dishwashers).
**Lifecycle:** Static configuration loaded at startup.
**Relationships:** Dictates which `Attribute`s are created.
**Fields:** `ATTRIBUTES` (schema), `EVIDENCE_TIER_WEIGHTS`, `CONFIDENCE_WEIGHTS`, `TEMPLATES`.
