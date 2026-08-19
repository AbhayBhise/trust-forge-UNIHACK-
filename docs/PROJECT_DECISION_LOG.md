**Version:** 2.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-18

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
**Status:** Evolved — currently includes retailer evidence for coverage.

## D-004 — No Hard Row Limit
**Decision:** Remove 25-row limit. Support parallel processing for large datasets.
**Reason:** Real-world datasets have 1000+ rows.
**Status:** Implemented (MAX_ROWS = 10,000).

## D-005 — Parallel Processing via ThreadPoolExecutor
**Decision:** Use ThreadPoolExecutor with configurable workers.
**Reason:** Sequential processing too slow for 1000+ rows with web evidence.
**Status:** Implemented (default 8 workers).

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
