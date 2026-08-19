**Version:** 3.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-18

# Technical Debt Log

All items resolved as of v0.8. No active debt remaining.

---

## TD-001 — Hardcoded Appliance Taxonomy → RESOLVED
Category config now defines all 50 attributes with UOM standards and VALID_VALUES.

## TD-002 — Hardcoded Feature Values → RESOLVED
Template generation derives features from verified attributes only.

## TD-003 — No Parallel Processing → RESOLVED
ThreadPoolExecutor with configurable workers (default 8).

## TD-004 — Row Limit Enforcement → RESOLVED
MAX_ROWS_PER_BATCH = 10,000. Background jobs process all rows.

## TD-005 — Single Evidence Source → RESOLVED
CompositeProvider chains Hardcoded → PDF → Web. Three sources.

## TD-006 — No Normalization → RESOLVED
Paper 1 implementation with 40+ rules, UOM enforcement.

## TD-007 — No HTML Spec Extraction → RESOLVED
Paper 2 implementation with wrapper induction, seed-based discovery.

## TD-008 — No Web Evidence → RESOLVED
Real-time scraping with per-MPN timeout, graceful degradation.

## TD-009 — No Progress Tracking → RESOLVED
Background job queue with SSE streaming. Frontend progress bar.

---

## Active Debt

None currently tracked.
