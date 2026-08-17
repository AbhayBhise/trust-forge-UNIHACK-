**Version:** 2.0  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Active  
**Last Updated:** 2026-08-17

# Project Decision Log

All architectural and engineering decisions for TrustForge.

---

## D-001 — Descriptions from Validated Facts Only
**Date:** 2026-08-14  
**Decision:** Descriptions are generated only from validated attributes.  
**Reason:** Generated text must never become a source of truth.  
**Alternatives:** Generate descriptions first, validate against evidence.  
**Trade-offs:** Lose LLM fluency for strict factual rigidity.  
**Status:** Locked.

---

## D-002 — Heuristic Confidence
**Date:** 2026-08-14  
**Decision:** Confidence is heuristic, calibrated against ground truth.  
**Reason:** LLM confidence is unreliable. Deterministic formula provides explainability.  
**Alternatives:** LLM self-reflection for 0-100 score.  
**Trade-offs:** Requires manual tuning per category, guarantees explainability.  
**Status:** Locked.

---

## D-003 — Manufacturer-First Evidence
**Date:** 2026-08-14  
**Decision:** Evidence retrieved manufacturer-first. Distributor sites excluded.  
**Reason:** Highest quality canonical truth, avoids circular references.  
**Alternatives:** Broad web search including Amazon, Home Depot.  
**Trade-offs:** More "missing evidence" gaps, but evidence is 100% trustworthy.  
**Status:** Evolved — now includes retailer evidence (Amazon, Home Depot, Lowe's) for better coverage, with manufacturer sources preferred.

---

## D-004 — No Hard Row Limit
**Date:** 2026-08-17  
**Decision:** Remove 25-row limit. Support parallel processing for large datasets.  
**Reason:** Real-world datasets have 1000+ rows. Hard limit blocks production use.  
**Alternatives:** Keep limit, require chunking.  
**Trade-offs:** More complex server architecture, but enables real-world scale.  
**Status:** Implemented.

---

## D-005 — Parallel Processing via ThreadPoolExecutor
**Date:** 2026-08-17  
**Decision:** Use ThreadPoolExecutor with configurable workers for parallel processing.  
**Reason:** Sequential processing too slow for 1000+ rows with web evidence.  
**Alternatives:** Async/await, multiprocessing, Celery.  
**Trade-offs:** Thread limits for I/O-bound tasks. Simple implementation for hackathon.  
**Status:** Implemented.

---

## D-006 — CompositeProvider Architecture
**Date:** 2026-08-16  
**Decision:** Chain evidence providers: Hardcoded → PDF → Web.  
**Reason:** Different MPNs have different evidence availability. Chaining maximizes coverage.  
**Alternatives:** Single provider, parallel providers.  
**Trade-offs:** Sequential fallback adds latency for unknown MPNs. Simple architecture.  
**Status:** Implemented.

---

## D-007 — Doc-First Philosophy
**Date:** 2026-08-14  
**Decision:** System must NEVER generate content from unvalidated information. If evidence not found, mark `needs_review` with 0% confidence.  
**Reason:** Prevents hallucination. Marketing descriptions generated deterministically from evidence-backed attributes only.  
**Alternatives:** Allow low-confidence generation, flag for review.  
**Trade-offs:** More `needs_review` items, but zero hallucination guaranteed.  
**Status:** Locked.

---

## D-008 — Enterprise White Theme
**Date:** 2026-08-17  
**Decision:** Redesign UI from dark template to white enterprise theme.  
**Reason:** Match Unilog brand style (Avenir font, blue primary, clean enterprise look).  
**Alternatives:** Keep dark theme, use generic styling.  
**Trade-offs:** More CSS work, but professional appearance for judges.  
**Status:** Implemented.

---

## D-009 — Background Job Queue
**Date:** 2026-08-17  
**Decision:** Add background job queue for large datasets with SSE streaming.  
**Reason:** Large datasets take minutes to process. Need progress feedback.  
**Alternatives:** Synchronous processing only, client-side polling.  
**Trade-offs:** More complex server, but better UX.  
**Status:** Implemented.
