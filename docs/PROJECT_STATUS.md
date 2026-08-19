**Version:** 4.0
**Date:** 2026-08-19
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-19

# Project Status Dashboard

---

## Release Tracking

| Version | Milestone | Status | Date |
|---------|-----------|--------|------|
| v0.1 | Pipeline Skeleton | Completed | 2026-08-14 |
| v0.2 | Evidence Retrieval | Completed | 2026-08-14 |
| v0.3 | Validation & Confidence | Completed | 2026-08-14 |
| v0.4 | Description Generation | Completed | 2026-08-14 |
| v0.5 | QA Audits & Determinism | Completed | 2026-08-15 |
| v0.6 | 252-Column Export | Completed | 2026-08-15 |
| v0.7 | Web Evidence Provider | Completed | 2026-08-16 |
| v0.8 | Parallel Processing | Completed | 2026-08-17 |
| v0.9 | Smart Column Detection | Completed | 2026-08-19 |
| v1.0 | Hackathon Submission | Ready | — |

---

## Module Status

### Identity Resolution
**Status:** Complete
**Tests:** test_pipeline (2 tests)

### Attribute Model & Configuration
**Status:** Complete
**Tests:** test_config_appliances (3 tests)

### Evidence Retrieval
**Status:** Complete
**Providers:** HardcodedRealDataProvider, PDFEvidenceProvider, WebEvidenceProvider, CompositeProvider
**Changes:** E-commerce sources removed (Amazon, HomeDepot, Lowe's). PDF hunting added. Persistent cache added. Timeouts reduced (5s per MPN).

### Normalization (Paper 1)
**Status:** Complete
**Tests:** test_new_modules (standalone)

### HTML Spec Extraction (Paper 2)
**Status:** Complete
**Tests:** test_new_modules (standalone)

### Validation & Confidence
**Status:** Complete
**Tests:** test_validation (3 tests)
**Changes:** Confidence weights rebalanced (title_match: 0.14→0.06, evidence_tier: 0.10→0.18)

### Description Generation
**Status:** Complete
**Tests:** test_pipeline (1 test)
**Changes:** 6 description types (Invoice, Mobile, Match, Short, Retail, Long) with character limits

### 252-Column Export Mapper
**Status:** Complete
**Tests:** test_mapper (1 test)

### Smart Column Detection
**Status:** Complete
**Module:** column_detector.py
**Tests:** test_column_detector (12 tests)
**Features:** Auto-maps any CSV column name to internal schema. Pattern matching, fuzzy matching, exact aliases. Handles MPN, Part_Number, model_number, etc.

### FastAPI Server
**Status:** Complete
**Routes:** 5 endpoints (process, jobs, job status, SSE stream, health)
**Changes:** Removed hardcoded REQUIRED_SCHEMA. Uses smart column detection. 24 workers (increased from 8). Returns column_map and warnings in responses.

### Frontend
**Status:** Complete
**Views:** 7 (dashboard, upload, diff, qa, journey, detail, explain)
**Changes:** Shows column detection results. Updated upload description to mention auto-detection.

---

## Test Files

| File | Type | Tests |
|------|------|-------|
| test_pipeline.py | unittest | 5 |
| test_models.py | unittest | 3 |
| test_config_appliances.py | unittest | 3 |
| test_validation.py | unittest | 3 |
| test_robustness.py | unittest | 4 |
| test_qa_audits.py | unittest | 4 |
| test_determinism.py | unittest | 3 |
| test_mapper.py | unittest | 1 |
| test_column_detector.py | unittest | 12 |
| test_new_modules.py | standalone | assertions |
| test_zero_evidence.py | standalone | assertions |

**Total:** 31+ tests passing

---

## Resolved Gaps (from UniHack session 2026-08-18)

1. **Source restriction**: Removed Amazon/HomeDepot/Lowe's — strictly using manufacturer domains.
2. **Category taxonomy**: System now accepts dynamic taxonomy assignment via `Classpath` column or keyword heuristics.
3. **Hardcoded provider**: Deprioritized `HardcodedRealDataProvider` as a last-resort fallback to avoid "mocked" data penalties.
4. **Missing output fields**: 4-5 description types, marketing desc, item features, and digital assets are now populated with correct formatting and sequence.
5. **LOV file**: Expanded hardcoded lookups mapping to more comprehensive valid values.
6. **Source URL traceability**: Ensured `source_url` is consistently and explicitly recorded across all providers.
7. **Flexible input**: Smart column detection accepts ANY CSV format (2026-08-19).
8. **Persistent cache**: Web evidence cached to disk for instant re-runs (2026-08-19).
9. **Faster processing**: Timeouts reduced, workers increased to 24 (2026-08-19).

---

## Known Gaps (2026-08-19)

1. **Missing reference files**: LOV, taxonomy, UOM, content guidelines not provided by Unilog. System works without them but cannot validate against controlled vocabularies.
2. **14K category taxonomy**: Only appliances category implemented. Need taxonomy file to expand.
3. **JS-rendered sites**: Web provider cannot scrape React/Angular sites (no headless browser).
4. **Ground truth**: Only 2 MPNs have ground truth (PDSH4816AF, WDTS7024RZ). Need 200-item file for full evaluation.
