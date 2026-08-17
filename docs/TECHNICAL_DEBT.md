**Version:** 1.1  
**Date:** 2026-08-14  
**Owner:** AI Pipeline  
**Status:** Active  
**Reviewed By:** User  
**Last Updated:** 2026-08-14  

# Technical Debt Log

This document tracks intentional architectural shortcuts and features we intentionally deferred. Every item here represents a known gap between the current implementation and the production-ready state.

---

## TD-001

**Title:** Hardcoded Appliance Taxonomy
**Files:** `pipeline.py`
**Priority:** Medium
**Risk:** Low (Acceptable for demo scope if limited to one category)
**Owner:** AI Pipeline

**Reason:**
Temporary implementation to allow end-to-end testing of the pipeline without a full classification model. Currently uses a naive substring match (`"dishwasher"` in `Part_Desc`).

**Replacement:**
LLM Classification Engine or mapping dictionary once the core pipeline is stable for multi-category processing.

---

## TD-002

**Title:** Hardcoded Feature Value for Template Generation
**Files:** `pipeline.py`
**Priority:** High
**Risk:** Medium (Hardcoded values will leak into descriptions for unmatched products)
**Owner:** AI Pipeline

**Reason:**
The feature `"CleanBoost™"` is currently hardcoded in the rendering context to demonstrate template rendering logic without building the complex marketing feature extraction logic.

**Replacement:**
Derive dynamic product features directly from the Evidence objects.
