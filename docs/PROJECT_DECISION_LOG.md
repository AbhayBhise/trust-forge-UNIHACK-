**Version:** 3.0
**Date:** 2026-08-19
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-19

# Project Decision Log

All architectural and engineering decisions for TrustForge.

---

## D-001 — Descriptions from Validated Facts Only
**Decision:** Descriptions generated only from validated attributes.
**Reason:** Generated text must never become a source of truth.
**Status:** Locked.

## D-002 — Heuristic Confidence
**Decision:** Confidence is heuristic, calibrated against ground truth.
**Reason:** LLM confidence is unreliable. Deterministic formula provides explainability.
**Status:** Locked.

## D-003 — Manufacturer-First Evidence
**Decision:** Evidence retrieved manufacturer-first. Distributor sites excluded.
**Reason:** Highest quality canonical truth, avoids circular references.
**Status:** Evolved — e-commerce sources (Amazon, HomeDepot, Lowe's) FORBIDDEN per Unilog guidelines (2026-08-19).

## D-004 — No Hard Row Limit
**Decision:** Remove 25-row limit. Support parallel processing for large datasets.
**Reason:** Real-world datasets have 1000+ rows.
**Status:** Implemented (MAX_ROWS = 10,000).

## D-005 — Parallel Processing via ThreadPoolExecutor
**Decision:** Use ThreadPoolExecutor with configurable workers.
**Reason:** Sequential processing too slow for 1000+ rows with web evidence.
**Status:** Implemented (increased from 8 to 24 workers, 2026-08-19).

## D-006 — CompositeProvider Architecture
**Decision:** Chain evidence providers: Hardcoded → PDF → Web.
**Reason:** Different MPNs have different evidence availability.
**Status:** Implemented.

## D-007 — Doc-First Philosophy
**Decision:** System must NEVER generate content from unvalidated information.
**Reason:** Prevents hallucination. Marketing descriptions from evidence-backed attributes only.
**Status:** Locked.

## D-008 — Enterprise White Theme
**Decision:** Redesign UI from dark to white enterprise theme.
**Reason:** Match Unilog brand style (Avenir font, blue primary).
**Status:** Implemented.

## D-009 — Background Job Queue
**Decision:** Add background job queue with SSE streaming for large datasets.
**Reason:** Large datasets need progress feedback.
**Status:** Implemented.

## D-010 — E-Commerce Sources Forbidden (2026-08-19)
**Decision:** Remove Amazon, HomeDepot, Lowe's from web_evidence_provider.py. Use manufacturer sites only.
**Reason:** Unilog guidelines explicitly forbid e-commerce sources. "Data sourced from shopping sites like Amazon, eBay are not considered valid."
**Status:** Implemented.

## D-011 — Smart Column Detection (2026-08-19)
**Decision:** Remove hardcoded REQUIRED_SCHEMA. Auto-detect columns from ANY CSV format.
**Reason:** Evaluators may upload CSVs with different column names. System must be flexible.
**Status:** Implemented.

## D-012 — Persistent Web Cache (2026-08-19)
**Decision:** Cache web evidence to disk (web_evidence_cache.json).
**Reason:** Second run should be instant. Avoid re-fetching same MPNs.
**Status:** Implemented.

## D-013 — Faster Processing (2026-08-19)
**Decision:** Reduce timeouts (8s→5s), increase workers (8→24), reduce delay (0.3s→0.2s).
**Reason:** Improve throughput from 0.3 to 0.5 rows/sec for hackathon demo.
**Status:** Implemented.

## D-014 — 6 Description Types (2026-08-19)
**Decision:** Add INVOICE (40 char), MOBILE (80), MATCH (120), SHORT (200), RETAIL (500), LONG (800) with character limits.
**Reason:** Unilog guidelines require 4-5 description types with strict character limits.
**Status:** Implemented.

## D-015 — Confidence Weights Rebalanced (2026-08-19)
**Decision:** Reduce title_match (0.14→0.06), increase evidence_tier (0.10→0.18).
**Reason:** Sparse CSV descriptions penalize accurate data; manufacturer PDFs are gold standard.
**Status:** Implemented.

## D-016 — PDF Hunting (2026-08-19)
**Decision:** Auto-find and extract PDF spec sheets from manufacturer pages.
**Reason:** PDFs provide highest quality evidence (tier 5).
**Status:** Implemented.

## D-017 — View Source Button (2026-08-19)
**Decision:** Every attribute with source_url gets a clickable link in frontend.
**Reason:** Transparency and audit trail for judges.
**Status:** Implemented.
