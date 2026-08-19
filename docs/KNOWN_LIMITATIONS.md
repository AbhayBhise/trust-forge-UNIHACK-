**Version:** 2.0
**Date:** 2026-08-19
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-19

# Known Limitations

This document tracks things the current system cannot solve by design. This is distinct from Technical Debt (which represents intentionally postponed work).

## 1. Non-OCR PDF Extraction
**Limitation:** Cannot extract information from scanned PDFs without OCR.
**Impact:** Image-based PDFs will fail to extract attributes.
**Reason:** PyMuPDF extracts raw text; no OCR layer is included.

## 2. Web Scraping Reliability
**Limitation:** Most manufacturer sites block automated HTTP requests (JS-rendered pages, CAPTCHAs, redirects).
**Impact:** Unknown MPNs may not retrieve web evidence, falling back to `needs_review` with 0% confidence.
**Reason:** Web scraping is best-effort. The pipeline gracefully degrades rather than fabricating data.
**Note:** E-commerce sites (Amazon, HomeDepot, Lowe's) are FORBIDDEN per Unilog guidelines.

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

## 8. Missing Reference Files
**Limitation:** LOV, taxonomy, UOM, content guidelines not provided by Unilog.
**Impact:** Cannot validate against controlled vocabularies or use approved abbreviations.
**Reason:** Files described in Solution Guide but not available for download.

## 9. Limited Ground Truth
**Limitation:** Only 2 MPNs have ground truth (PDSH4816AF, WDTS7024RZ).
**Impact:** Cannot measure accuracy across full 200-item dataset.
**Reason:** Full 200-item file not available.

## 10. JS-Rendered Sites
**Limitation:** Cannot scrape React/Angular/SPA sites (no headless browser).
**Impact:** Many modern manufacturer sites return blank HTML.
**Reason:** Would require Playwright/Selenium; not included in hackathon scope.

---

### Note on Fixture Provenance
- **The extraction pipeline is real**: PyMuPDF parses real PDF documents during execution.
- **Fixture Data**: The current Whirlpool PDF (`whirlpool_spec_sheet.pdf`) is a synthetic reference fixture for demonstrating the end-to-end extraction workflow.
- **Web Evidence**: Real data retrieved from manufacturer sites only (e-commerce FORBIDDEN). Most sites block automated requests, so extraction rate is low for unknown MPNs.
- **Smart Column Detection**: Accepts ANY CSV format via pattern matching, fuzzy matching, and exact aliases.
