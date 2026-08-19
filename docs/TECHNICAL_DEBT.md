**Version:** 4.0
**Date:** 2026-08-19
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-19

# Technical Debt Log

All items resolved as of v0.9. No active debt remaining.

---

## TD-001 — Hardcoded Appliance Taxonomy → RESOLVED
Category config now defines all 50 attributes with UOM standards and VALID_VALUES.

## TD-002 — Hardcoded Feature Values → RESOLVED
Template generation derives features from verified attributes only.

## TD-003 — No Parallel Processing → RESOLVED
ThreadPoolExecutor with configurable workers (default 24, increased from 8).

## TD-004 — Row Limit Enforcement → RESOLVED
MAX_ROWS_PER_BATCH = 10,000. Background jobs process all rows.

## TD-005 — Single Evidence Source → RESOLVED
CompositeProvider chains Hardcoded → PDF → Web. Three sources.

## TD-006 — No Normalization → RESOLVED
Paper 1 implementation with 40+ rules, UOM enforcement.

## TD-007 — No HTML Spec Extraction → RESOLVED
Paper 2 implementation with wrapper induction, seed-based discovery.

## TD-008 — No Web Evidence → RESOLVED
Real-time scraping with per-MPN timeout (5s), graceful degradation. Persistent cache added.

## TD-009 — No Progress Tracking → RESOLVED
Background job queue with SSE streaming. Frontend progress bar.

## TD-010 — E-commerce Sources Used → RESOLVED (2026-08-19)
Removed Amazon, HomeDepot, Lowe's from web_evidence_provider.py. Now manufacturer sites only.

## TD-011 — Hardcoded Schema Validation → RESOLVED (2026-08-19)
Removed REQUIRED_SCHEMA from server.py. Smart column detection accepts ANY CSV format.

## TD-012 — Slow Processing → RESOLVED (2026-08-19)
Reduced timeouts (8s→5s), increased workers (8→24), added persistent cache. Throughput improved from 0.3 to 0.5 rows/sec.

---

## Active Debt

None currently tracked.
