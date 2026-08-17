**Version:** 1.2  
**Date:** 2026-08-14  
**Owner:** AI Pipeline  
**Status:** Active  
**Reviewed By:** User  
**Last Updated:** 2026-08-14  

# Project Decision Log

This document serves as the single source of truth for all architectural and engineering decisions made during the development of the Product Trust Engine. 

---

## Decision D-001

**Date:** 2026-08-14
**Owner:** AI Pipeline
**Module:** Architecture
**Decision:** Descriptions are generated only from validated facts.
**Reason:** Generated text must never become a source of truth.
**Alternatives Considered:** Generate descriptions first, then validate the text against evidence.
**Trade-offs:** We lose some of the natural fluency of LLM-generated text in favor of strict factual rigidity.
**Affected Files:** `pipeline.py`, `models.py`
**Issue Reference:** Robustness Audit #1
**Status:** Locked.

---

## Decision D-002

**Date:** 2026-08-14
**Owner:** AI Pipeline
**Module:** Confidence Engine
**Decision:** Confidence is heuristic and calibrated against the ground truth dataset.
**Reason:** LLM confidence is unreliable. A deterministic formula weighted by evidence tier, attribute source matching, and validation rules provides better explainability.
**Alternatives Considered:** Using LLM self-reflection to output a 0-100 score.
**Trade-offs:** Heuristics require manual tuning per category, but guarantee explainability and determinism.
**Affected Files:** `config_appliances.py`, `pipeline.py`
**Issue Reference:** Confidence Calibration
**Status:** Locked.

---

## Decision D-003

**Date:** 2026-08-14
**Owner:** AI Pipeline
**Module:** Evidence Retrieval
**Decision:** Evidence must be retrieved manufacturer-first. Distributor sites are excluded.
**Reason:** Ensures the highest quality and most canonical truth, avoiding circular references from unverified distributor networks.
**Alternatives Considered:** Broad web search including Amazon, Home Depot, Grainger.
**Trade-offs:** We will have more "missing evidence" gaps, but the evidence we do have will be 100% trustworthy.
**Affected Files:** `evidence_provider.py`
**Issue Reference:** Traceability Audit
**Status:** Locked.


### DECISION: Fix Correctness Bugs (Fabricated Values & Export Alignment)
- **Context**: A regression check found fabricated values ("5-Wash Cycle", "CleanBoost") and misaligned export slots.
- **Root Cause (Fabrication)**: "CleanBoost" was hardcoded in `pipeline.py`. "5 Wash Cycles" was correctly extracted by the pipeline, but the mock PDF fixture itself contained fabricated data.
- **Root Cause (Alignment)**: `export_mapper.py` compacted slots by skipping missing attributes.
- **Fix**: Removed hardcoded values, regenerated the synthetic PDF fixture to strictly match ground truth, and rewrote the export mapper to use a fixed index mapping.

