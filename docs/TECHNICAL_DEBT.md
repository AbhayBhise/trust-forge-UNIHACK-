**Version:** 1.1  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Active  
**Last Updated:** 2026-08-17

# Technical Debt Log

This document tracks intentional architectural shortcuts and features we intentionally deferred.

---

## TD-001 — Hardcoded Appliance Taxonomy
**Status:** Resolved (v0.8)  
**Files:** `pipeline.py`, `config_appliances.py`  
**Resolution:** Category config now defines all 50 attributes with UOM standards and VALID_VALUES. Taxonomy is data-driven, not hardcoded.

---

## TD-002 — Hardcoded Feature Values
**Status:** Resolved (v0.8)  
**Files:** `pipeline.py`  
**Resolution:** Template generation now derives features from verified attributes only. No hardcoded marketing strings.

---

## TD-003 — No Parallel Processing
**Status:** Resolved (v0.8)  
**Files:** `server.py`, `run_batch.py`  
**Resolution:** ThreadPoolExecutor with configurable workers (default 8). Background job queue with progress tracking.

---

## TD-004 — Row Limit Enforcement
**Status:** Resolved (v0.8)  
**Files:** `server.py`  
**Resolution:** MAX_ROWS_PER_BATCH = 10000. Background jobs process all rows without hard limits.

---

## TD-005 — Single Evidence Source
**Status:** Resolved (v0.7)  
**Files:** `evidence_provider.py`, `web_evidence_provider.py`, `eval.py`  
**Resolution:** CompositeProvider chains Hardcoded → PDF → Web. Three evidence sources with graceful degradation.

---

## TD-006 — No Normalization
**Status:** Resolved (v0.7)  
**Files:** `normalizer.py`  
**Resolution:** Paper 1 implementation with 40+ rules, UOM enforcement, canonical value mapping.

---

## TD-007 — No HTML Spec Extraction
**Status:** Resolved (v0.7)  
**Files:** `html_spec_extractor.py`  
**Resolution:** Paper 2 implementation with wrapper induction, seed-based discovery, spec block detection.

---

## TD-008 — No Web Evidence
**Status:** Resolved (v0.7)  
**Files:** `web_evidence_provider.py`  
**Resolution:** Real-time scraping of Amazon, Home Depot, Lowe's, manufacturer sites. Per-MPN timeout, graceful degradation.

---

## TD-009 — No Progress Tracking
**Status:** Resolved (v0.8)  
**Files:** `server.py`, `frontend/app.js`  
**Resolution:** Background job queue with SSE streaming. Frontend shows progress bar, verified/needs_review counts, rows/sec, ETA.

---

## Active Debt

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| — | None | — | All resolved |
