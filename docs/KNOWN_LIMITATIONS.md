**Version:** 1.0  
**Date:** 2026-08-14  
**Owner:** AI Pipeline  
**Status:** Active  
**Reviewed By:** User  
**Last Updated:** 2026-08-14  

# Known Limitations

This document tracks things the current system cannot solve by design. This is distinct from Technical Debt (which represents intentionally postponed work). 

These limitations demonstrate engineering maturity and set clear boundaries for the system's capabilities.

## 1. Non-OCR PDF Extraction
**Limitation:** Cannot extract information from scanned PDFs without OCR.
**Impact:** If a manufacturer provides only image-based PDFs, the pipeline will fail to extract attributes and confidence will degrade.
**Reason:** The current `EvidenceProvider` relies on raw text extraction for determinism and speed.

## 2. Official Documentation Dependency
**Limitation:** Cannot verify manufacturer data if official documentation is unavailable.
**Impact:** Unbranded, generic, or obscure products without an accessible official manufacturer page will score very low on evidence completeness.
**Reason:** The system enforces a strict "manufacturer-first" evidence policy; distributor and marketplace sites are intentionally excluded to prevent circular validation.

## 3. Heuristic Confidence Calibration
**Limitation:** Confidence is heuristic and calibrated only against the provided 200-item ground truth.
**Impact:** Confidence scores may drift or require manual recalibration when introducing entirely new product categories with different data patterns.
**Reason:** Heuristic confidence ensures full explainability and deterministic behavior, avoiding opaque LLM confidence scores.

## 4. Category Specialization
**Limitation:** Currently optimized exclusively for the Appliances configuration.
**Impact:** Running the pipeline on highly divergent categories (e.g., Fasteners, Chemicals) will require writing new category configurations (`config_*.py`).
**Reason:** This is a structural choice to ensure deep, high-quality validation rather than shallow, generic parsing.

## 5. Excluded Sources
**Limitation:** Marketplace websites (Amazon, Home Depot, distributor portals) are intentionally excluded.
**Impact:** Evidence coverage may be lower than a generic web search.
**Reason:** Marketplaces often contain user-generated or aggregated errors. The architecture mandates single-source-of-truth extraction.


### Note on Fixture Provenance
- **The extraction pipeline is real**: PyMuPDF parses a real PDF document during execution.
- **Fixture Data**: The current Whirlpool PDF (`whirlpool_spec_sheet.pdf`) is a **synthetic reference fixture** created purely for demonstrating the complete end-to-end extraction workflow. It contains only ground-truth-supported data.
- **Future Work**: Live manufacturer PDF retrieval (web scraping/API) is outside the current project scope and is documented as future work.

