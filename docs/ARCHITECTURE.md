**Version:** 3.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-18

# System Architecture

## System Diagram
```mermaid
graph TD
    A[Raw Input CSV] --> B[Deduplication]
    B --> C[Identity Resolution]
    C --> D{Evidence Provider}
    D --> E[WebEvidenceProvider]
    D --> F[PDFEvidenceProvider]
    D --> G[HardcodedRealDataProvider (Fallback)]
    E --> H[Evidence Bundle]
    F --> H
    G --> H
    H --> I[Attribute Extraction]
    I --> J[Normalization - Paper 1]
    J --> K[Cross-Validation]
    K --> L[Validation & UOM Enforcement]
    L --> M[Confidence Scoring]
    M --> N[Description Generation]
    N --> O[Quality Score Computation]
    O --> P[Product Model]
    P --> Q[252-Column Mapper]
    Q --> R[Delivery Format CSV]
```

## Pipeline Steps (in execution order)

| Step | Function | Description |
|------|----------|-------------|
| 1 | `deduplicate()` | Normalize MPN (uppercase, strip hyphens), deduplicate rows |
| 2 | `resolve_identity()` | Check brand placeholders, determine verified/unverified |
| 3 | `provider.fetch(mpn)` | Chain: Web → PDF → Hardcoded (Fallback) evidence retrieval |
| 4 | Attribute extraction | Map evidence facts to 50 category attributes |
| 5 | `normalize_product_attributes()` | Paper 1: canonical value mapping, UOM enforcement |
| 6 | Cross-validation | Compare values against multiple evidence sources |
| 7 | Validation | Enum checks, UOM pattern matching, required field checks |
| 8 | Confidence scoring | Multi-factor: identity, evidence tier, title match, UOM, validation |
| 9 | Description generation | Deterministic templates from verified attributes only |
| 10 | Quality score | Compute completeness, validation pass rate, mean confidence |

## Module Responsibilities

### Core Pipeline
- **`models.py`**: Dataclasses — Product, Attribute, Identity, Evidence, ValidationEntry, HistoryEntry. Contains `to_dict()` serialization and `get_attr()` lookup.
- **`pipeline.py`**: 10-step deterministic pipeline. Dedup → Identity → Evidence → Extract → Normalize → Cross-validate → Validate → Score → Describe → Quality.
- **`config_appliances.py`**: Category config — 26+ attributes with APPROVED_UOM, UOM_PATTERNS, VALID_VALUES, confidence weights, 5 description templates (Mobile, Match, Short, Long, Retail).

### Evidence Providers
- **`evidence_provider.py`**: Abstract base class + `HardcodedRealDataProvider` (pre-fetched facts for 2 known MPNs).
- **`pdf_evidence_provider.py`**: Extracts specs from manufacturer PDFs via PyMuPDF.
- **`web_evidence_provider.py`**: Real-time web scraping — Direct manufacturer sites only (e-commerce forbidden). Per-MPN timeout (8s), graceful degradation.
- **`eval.py`**: `CompositeProvider` — chains Web → PDF → Hardcoded (fallback only).

### Research Paper Implementations
- **`normalizer.py`**: Paper 1 (More, WalmartLabs 2016) — 40+ normalization rules, UOM enforcement, canonical value mapping.
- **`html_spec_extractor.py`**: Paper 2 (Gangadhar & Kulkarni 2022) — HTML spec block detection, wrapper induction, seed-based attribute discovery.

### Export & Server
- **`export_mapper.py`**: Flattens Product model to 252-column CSV.
- **`server.py`**: FastAPI with 5 routes, parallel processing (8 workers), background job queue, progress tracking, SSE streaming.
- **`run_batch.py`**: Offline batch processor with ThreadPoolExecutor.

### Frontend
- **`frontend/`**: Enterprise white-themed SPA — sidebar navigation, dashboard, CSV upload with drag-drop, product detail, pipeline journey, ground truth diff, QA metrics.

## Folder Structure
```
trust-forge/
├── files/
│   ├── models.py                     # Core dataclasses (Product, Attribute, Identity, Evidence, etc.)
│   ├── pipeline.py                   # 10-step deterministic pipeline
│   ├── config_appliances.py          # Category config + UOM + VALID_VALUES
│   ├── evidence_provider.py          # Abstract base + hardcoded provider
│   ├── pdf_evidence_provider.py      # PDF extraction (PyMuPDF)
│   ├── web_evidence_provider.py      # Real-time web scraping
│   ├── html_spec_extractor.py        # Paper 2: HTML spec extraction
│   ├── normalizer.py                 # Paper 1: Attribute normalization
│   ├── eval.py                       # CompositeProvider + evaluation
│   ├── evaluator.py                  # Evaluation framework
│   ├── export_mapper.py              # 252-column CSV export
│   ├── mismatch_classifier.py        # Mismatch classification
│   ├── validate_ground_truth.py      # Ground truth validation report
│   ├── server.py                     # FastAPI + job queue + parallel (5 routes)
│   ├── run_batch.py                  # Batch processing with workers
│   └── test_*.py                     # 13 test files (26+ tests)
├── frontend/
│   ├── index.html                    # SPA shell with sidebar
│   ├── app.js                        # 7 views + job polling
│   ├── styles.css                    # White enterprise theme
│   └── categories.html               # Architecture explanation
├── docs/                             # This documentation
├── requirements.txt                  # Dependencies
└── README.md                         # Project overview
```

## Performance Characteristics
- **Hardcoded provider**: ~3,000 rows/sec (instant lookup)
- **Web provider**: ~0.3 rows/sec (limited by HTTP timeouts)
- **Parallel processing**: 8 workers via ThreadPoolExecutor
- **Graceful degradation**: Unknown MPNs → `needs_review` with 0% confidence
- **Zero hallucination**: Doc-First compliant — no values generated from unvalidated context
