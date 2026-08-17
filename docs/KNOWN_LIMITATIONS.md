**Version:** 1.1  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Active  
**Last Updated:** 2026-08-17

# Known Limitations

This document tracks things the current system cannot solve by design. This is distinct from Technical Debt (which represents intentionally postponed work).

## 1. Non-OCR PDF Extraction
**Limitation:** Cannot extract information from scanned PDFs without OCR.
**Impact:** Image-based PDFs will fail to extract attributes.
**Reason:** PyMuPDF extracts raw text; no OCR layer is included.

## 2. Web Scraping Reliability
**Limitation:** Most manufacturer/retailer sites block automated HTTP requests (JS-rendered pages, CAPTCHAs, redirects).
**Impact:** Unknown MPNs may not retrieve web evidence, falling back to `needs_review` with 0% confidence.
**Reason:** Web scraping is best-effort. The pipeline gracefully degrades rather than fabricating data.

## 3. Category Specialization
**Limitation:** Currently optimized exclusively for the Appliances configuration.
**Impact:** Running on divergent categories (Fasteners, Chemicals) requires new `config_*.py` files.
**Reason:** Deep, high-quality validation per category vs. shallow generic parsing.

## 4. Heuristic Confidence Calibration
**Limitation:** Confidence is heuristic and calibrated against the provided 200-item ground truth.
**Impact:** Scores may drift for entirely new product categories.
**Reason:** Heuristic confidence ensures full explainability and deterministic behavior.

## 5. Single-Category Scope
**Limitation:** Only one category configuration exists (appliances).
**Impact:** Multi-category support requires writing new config files.
**Reason:** Scoped to hackathon requirements; architecture supports expansion.

## 6. No Database Persistence
**Limitation:** Pipeline is stateless — results are JSON/CSV only.
**Impact:** No historical tracking, no incremental updates, no versioning.
**Reason:** Hackathon scope; production would add PostgreSQL or similar.

## 7. No Real-Time Processing
**Limitation:** Batch-only processing via API or CLI.
**Impact:** Cannot process streaming or event-driven inputs.
**Reason:** Batch architecture chosen for determinism and simplicity.

---

### Note on Fixture Provenance
- **The extraction pipeline is real**: PyMuPDF parses real PDF documents during execution.
- **Fixture Data**: The current Whirlpool PDF (`whirlpool_spec_sheet.pdf`) is a synthetic reference fixture for demonstrating the end-to-end extraction workflow.
- **Web Evidence**: Real data retrieved from Amazon, Home Depot, Lowe's, and manufacturer sites. Most sites block automated requests, so extraction rate is low for unknown MPNs.
