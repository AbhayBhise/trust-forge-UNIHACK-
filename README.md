# TrustForge — UniHack Product Trust Engine

An AI-powered product intelligence engine that transforms sparse distributor CSV inputs (6 columns, 1000+ rows) into 252-column commerce-ready catalogs with evidence-backed extraction and zero hallucination. Built for the UniHack challenge.

![Pipeline Overview](docs/pipeline_diagram.svg)

## The Problem
B2B distributors receive product data from hundreds of manufacturers, often in inconsistent formats with missing attributes, mismatched units, and marketing fluff. Manual review is too slow, and traditional LLM approaches introduce hallucination risk. TrustForge solves this by enforcing a deterministic, evidence-first approach: *No fact is accepted without manufacturer proof, and no description is generated without validated facts.*

## Architecture
1. **Smart Column Detection:** Auto-maps ANY CSV column name to internal schema (pattern matching, fuzzy matching, exact aliases)
2. **10-step Pipeline:** CSV → Dedup → Identity → Evidence → Extract → Normalize → Cross-validate → Validate → Score → Describe → Quality Score
3. **Data Model:** `Product` object tracking `Evidence`, `Attributes`, `ValidationReport`, and `HistoryEntry` per field
4. **Evidence Retrieval:** CompositeProvider chains Hardcoded → PDF → Web scraping (manufacturer sites only, e-commerce FORBIDDEN)
5. **Confidence System:** Heuristic formula (Tier × Consistency × Completion) — 100% reproducible, no LLM variance
6. **Research Papers:** Paper 1 (More, WalmartLabs 2016) normalization + Paper 2 (Gangadhar & Kulkarni 2022) HTML spec extraction

## Features
- **Smart Column Detection:** Upload ANY CSV format — system auto-detects MPN, manufacturer, brand, description columns
- **Zero Hallucination:** Unknown MPNs → `needs_review` with 0% confidence — never fabricates data
- **Evidence Traceability:** Every attribute has source URL, tier, and retrieval timestamp. View Source buttons.
- **Parallel Processing:** 24-worker ThreadPoolExecutor with background job queue and SSE progress streaming
- **Persistent Cache:** Web evidence cached to disk for instant re-runs
- **6 Description Types:** Invoice (40), Mobile (80), Match (120), Short (200), Retail (500), Long (800) with character limits
- **Enterprise Dashboard:** White-themed SPA with 7 views, CSV upload with drag-drop, progress bar, QA metrics
- **Manufacturer-Only Evidence:** No e-commerce sources (Amazon, etc.) — compliant with Unilog guidelines

## Demo & Installation
```bash
pip install -r requirements.txt

# Start server (serves both API and frontend)
cd files
python server.py

# Open http://127.0.0.1:8000/frontend/
```

## Performance
| Metric | Value | Change |
|--------|-------|--------|
| Hardcoded provider | ~3,000 rows/sec | — |
| Web provider | ~0.5 rows/sec | Improved from 0.3 |
| Parallel (24 workers) | ~0.5 rows/sec (mixed) | Improved from 0.3 |
| Persistent cache | instant | New |
| Determinism | Byte-identical over 10 runs | — |

## Folder Structure
```
trust-forge/
├── files/              # Core pipeline, server, tests
│   ├── models.py                     # Core dataclasses
│   ├── pipeline.py                   # 10-step deterministic pipeline
│   ├── config_appliances.py          # Category config + UOM + VALID_VALUES + 6 description templates
│   ├── column_detector.py            # Smart column detection for flexible CSV input (NEW)
│   ├── evidence_provider.py          # Abstract base + hardcoded provider
│   ├── pdf_evidence_provider.py      # PDF extraction
│   ├── web_evidence_provider.py      # Real-time web scraping + PDF hunting + persistent cache
│   ├── html_spec_extractor.py        # Paper 2: HTML spec extraction
│   ├── normalizer.py                 # Paper 1: Attribute normalization
│   ├── eval.py                       # CompositeProvider + evaluation
│   ├── export_mapper.py              # 252-column CSV export
│   ├── server.py                     # FastAPI + job queue + parallel (24 workers)
│   ├── run_batch.py                  # Batch processing with workers
│   ├── web_evidence_cache.json       # Persistent disk cache for web evidence (NEW)
│   └── test_*.py                     # 14 test files (31+ tests)
├── frontend/           # Enterprise white-themed SPA
├── docs/               # Architecture, API, data model, status
├── requirements.txt
└── README.md
```

## Test Suite
```bash
# Run all tests (31+ passing)
cd files
python -m unittest test_pipeline test_models test_config_appliances test_validation test_robustness test_mapper test_column_detector -v
```

## Known Limitations
- Web scraping unreliable for JS-rendered manufacturer sites (graceful degradation)
- Only appliances category configured (~1 of ~14,000 taxonomy categories)
- Stateless JSON/CSV — no database persistence
- No OCR for scanned PDFs
- Missing reference files (LOV, taxonomy, UOM, content guidelines)
