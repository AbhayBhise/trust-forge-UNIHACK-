# TrustForge — UniHack Product Trust Engine

An AI-powered product intelligence engine that transforms sparse distributor CSV inputs (6 columns, 1000+ rows) into 252-column commerce-ready catalogs with evidence-backed extraction and zero hallucination. Built for the UniHack challenge.

![Pipeline Overview](docs/pipeline_diagram.svg)

## The Problem
B2B distributors receive product data from hundreds of manufacturers, often in inconsistent formats with missing attributes, mismatched units, and marketing fluff. Manual review is too slow, and traditional LLM approaches introduce hallucination risk. TrustForge solves this by enforcing a deterministic, evidence-first approach: *No fact is accepted without manufacturer proof, and no description is generated without validated facts.*

## Architecture
1. **10-step Pipeline:** CSV → Dedup → Identity → Evidence → Extract → Normalize → Cross-validate → Validate → Score → Describe → Quality Score
2. **Data Model:** `Product` object tracking `Evidence`, `Attributes`, `ValidationReport`, and `HistoryEntry` per field
3. **Evidence Retrieval:** CompositeProvider chains Hardcoded → PDF → Web scraping
4. **Confidence System:** Heuristic formula (Tier × Consistency × Completion) — 100% reproducible, no LLM variance
5. **Research Papers:** Paper 1 (More, WalmartLabs 2016) normalization + Paper 2 (Gangadhar & Kulkarni 2022) HTML spec extraction

## Features
- **Explainability:** Click any field to see source URL, evidence snippet, confidence score, and validation rules
- **Graceful Degradation:** Missing evidence → `needs_review` with 0% confidence — never hallucinates
- **Parallel Processing:** 8-worker ThreadPoolExecutor with background job queue and SSE progress streaming
- **Enterprise Dashboard:** White-themed SPA with 7 views, CSV upload with drag-drop, progress bar, QA metrics

## Demo & Installation
```bash
pip install -r requirements.txt

# Start server (serves both API and frontend)
cd files
python server.py

# Open http://127.0.0.1:8000/frontend/
```

## Performance
| Metric | Value |
|--------|-------|
| Hardcoded provider | ~3,000 rows/sec |
| Web provider | ~0.3 rows/sec |
| Parallel (8 workers) | ~0.3 rows/sec (mixed) |
| Determinism | Byte-identical over 10 runs |

## Folder Structure
```
trust-forge/
├── files/              # Core pipeline, server, tests
├── frontend/           # Enterprise white-themed SPA
├── docs/               # Architecture, API, data model, status
├── requirements.txt
└── README.md
```

## Known Limitations
- Web scraping unreliable for JS-rendered manufacturer sites (graceful degradation)
- Only appliances category configured (~1 of ~14,000 taxonomy categories)
- Stateless JSON/CSV — no database persistence
- No OCR for scanned PDFs
