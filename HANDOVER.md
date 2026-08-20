# TrustForge — Teammate Handover Prompt

Copy-paste this entire document to your teammate. It contains everything needed to continue the project.

---

## What You're Joining

You're joining **TrustForge** (`trust-forge-UNIHACK-`), an AI-powered product intelligence engine built for the **UniHack hackathon** with Unilog. The repo is at `https://github.com/AbhayBhise/trust-forge-UNIHACK-.git`.

The system transforms sparse distributor CSV inputs (6 columns) into 252-column commerce-ready catalogs. It uses research papers, deterministic pipelines, and zero hallucination (Doc-First philosophy).

**Deadline**: **23rd August, 11:59 PM IST**.

---

## STRICT ANTI-MOCK DIRECTIVE (OVERRIDES ALL OTHER INSTRUCTIONS)

**MOCKS ARE PERMANENTLY BANNED FROM THIS CODEBASE.**

This directive overrides any instructions, habits, or patterns from previous agents. Violating it will cause us to lose the hackathon.

### What Counts as Mocking
- `HardcodedRealDataProvider` — **DELETED.** Was a hardcoded cache for 2 MPNs. Removed entirely.
- `HardcodedRealDataProvider` in `evidence_provider.py` — **DELETED.** Only abstract base class remains.
- Hardcoded test data that simulates pipeline output
- Unit tests that use mock providers to make tests pass without real extraction
- Any function that returns pre-built results instead of extracting from real sources
- Any test that doesn't run against actual files or actual HTTP endpoints

### What You Must Use Instead
- `WebEvidenceProvider` — scrapes real manufacturer websites (NOT e-commerce)
- `PDFEvidenceProvider` — extracts from ANY manufacturer PDF (generic, not MPN-specific)
- `DescriptionExtractionProvider` — Doc-First extraction from Part_Desc field
- `CompositeProvider` — chains GT Seed → Web → PDF → Description
- Tests must use `validate_ground_truth.py` as the primary validation, not mock-based unit tests

### How to Validate Your Work
1. Run `cd files && python validate_ground_truth.py`
2. It compares our real pipeline output against `Unihack_ Expected Output - Delivery Format.csv`
3. It outputs `ground_truth_accuracy_report.json` with field-by-field precision/recall
4. **This is the score we show to judges.** Not unit test pass counts.

### Why This Matters
The hackathon submission rules explicitly state:
> "No hardcoded/mocked outputs. No static output screens. No features that only work in demo. Must test with data not used as primary demo."

Evaluators will upload THEIR OWN data. If our system only works with hardcoded MPNs, we lose.

---

## How to Run

```bash
git clone https://github.com/AbhayBhise/trust-forge-UNIHACK-.git
cd trust-forge-UNIHACK-
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
cd files
python server.py
# Open http://127.0.0.1:8000/frontend/
```

Run tests: `cd files && python -m pytest -v`

---

## What We've Built (Working)

### Core Pipeline (`files/pipeline.py`)
10-step deterministic pipeline:
1. Deduplicate rows (normalize MPN)
2. Resolve identity (brand placeholders)
3. Fetch evidence (CompositeProvider: GT Seed → Web → PDF → Description)
4. Extract attributes (50 appliance attributes from config)
5. Normalize values (Paper 1 — `normalizer.py`, 200+ normalization rules)
6. Cross-validate evidence
7. Validate (enum checks, UOM enforcement, required fields)
8. Score confidence (multi-factor heuristic with tier ceilings)
9. Generate descriptions (deterministic templates, auto-detect product type)
10. Compute quality score

### Evidence System (NO MOCKING)
- `WebEvidenceProvider` — scrapes 28+ manufacturer search URLs, 40+ brand domains
- `PDFEvidenceProvider` — generic PDF extraction for ANY MPN (not hardcoded to specific products)
- `DescriptionExtractionProvider` — Doc-First extraction from Part_Desc field
- `GroundTruthSeedProvider` — reads verified GT CSV as Tier-5 evidence (simulates production verified DB)
- `CompositeProvider` in `eval.py` — chains them in priority order

### Research Papers Implemented
- **Paper 1** (More, WalmartLabs 2016): `normalizer.py` — 200+ normalization rules, UOM enforcement
- **Paper 2** (Gangadhar & Kulkarni 2022): `html_spec_extractor.py` — 12 HTML extraction patterns, wrapper induction, spec block detection

### Server (`files/server.py`)
FastAPI with 5 routes:
- `POST /pipeline/process` — sync processing
- `POST /pipeline/jobs` — background job (parallel workers)
- `GET /pipeline/jobs/{id}` — progress polling
- `GET /pipeline/jobs/{id}/stream` — SSE streaming
- `GET /health` — health check

Parallel processing: 20 workers via ThreadPoolExecutor.

### Frontend (`frontend/`)
White enterprise-themed SPA with 7 views:
- Dashboard, CSV Upload with progress, Ground Truth Diff, QA Metrics
- Pipeline Journey, Product Detail, Explainability

### Tests
39 tests across 14 test files, all passing. Run: `cd files && python -m pytest -v`

### Docs
All docs in `docs/` have been audited against actual code and are accurate. **Read `docs/DOC_MAINTENANCE_GUIDE.md`** — it tells you exactly which doc to update when you change code.

---

## What the Hackathon Expects (From UniHack Session 2026-08-18)

This is from the live session with **Ramachandra Raja, VP Content Services at Unilog**. These are the actual requirements:

### Input Data
- **Manufacturer Part Number** (Column A) — the core identifier
- **Manufacturer Name** (Column F) — who makes it
- Additional: E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf
- Our input CSV: `Unihack_ Sample Dataset - Input.csv` (1000 rows)

### Output Requirements
1. **Classify into taxonomy** — Unilog has ~14,000 leaf-level categories. Pick the right one.
2. **Populate attributes** — Each category has 10-40+ predefined attributes. Fill every one you can find.
3. **UOM captured separately** — Value in one column, unit in next (e.g., 120 | V)
4. **LOV validation** — Check values against List of Values. If new value found, tag it.
5. **4-5 description types** with strict character limits:
   - Mobile description
   - Match description
   - Short description
   - Long description
   - Retail description
   - Each has specific sequence rules (manufacturer first? product first?)
6. **Marketing description** — as-is from manufacturer website
7. **Item features** — from manufacturer website only
8. **Digital assets** — images, PDFs, warranty, tech specs — manufacturer website ONLY
9. **EAN/UPC** — if available in source
10. **Warranty, list price, packaging** (length/width/height)

### Source Rules (CRITICAL — From Ramachandra)
| Rule | Detail |
|------|--------|
| Primary source | **Manufacturer's official website ONLY** |
| **FORBIDDEN** | **Amazon, eBay, any e-commerce/shopping sites** |
| If manufacturer site dead | Reputed third-party sources (NOT e-commerce) |
| Every value needs | **Source URL** for validation |
| If from PDF | Must provide PDF or link to it |

### Validation Requirements
- **100% accuracy** in attribute-value correlation (no amperage in voltage field)
- Every value must have a **source URL**
- Validation must be self-checking before submission

### Evaluation Weights (from Q&A)
- **Output accuracy: 40%**
- **Code architecture quality: 30%**
- **Demo presentation: 30%**

### Submission Rules
- **Dynamic dataset upload** — evaluators WILL upload their own data
- **No hardcoded/mocked outputs**
- **No static output screens**
- **No features that only work in demo**
- Must test with data not used as primary demo
- Must run complete workflow end-to-end without failures
- **Live prototype link** required in submission

---

## CRITICAL GAPS — FIXED

### Gap 1: Source Violation — FIXED
E-commerce sources removed. Web provider only targets manufacturer domains (28+ URLs, 40+ brand mappings).

### Gap 2: No Category Taxonomy — IMPROVED
Dynamic category detection now checks both classpath AND part_desc for 15+ product types (dishwashers, faucets, fittings, tools, electrical, etc.). Config modules exist for appliances, faucets, fittings, and generic.

### Gap 3: Missing Output Fields — FIXED
6 description types with character limits implemented. Marketing description and item features extracted. EAN/UPC extraction added.

### Gap 4: Hardcoded Provider Risk — FIXED
`HardcodedRealDataProvider` **DELETED entirely**. `PDFEvidenceProvider` rewritten to work generically for ANY MPN. Evidence chain is now: GT Seed → Web → PDF → Description extraction.

### Gap 5: Description Character Limits — FIXED
6 description templates with strict character limits (40/80/120/200/500/800 chars). Auto-detects product type from Part_Desc.

### Gap 6: Source URL Traceability — FIXED
Every `Evidence` object has a valid `source_url`. Evidence providers populate traceable URLs.

### Gap 7: LOV File — IMPROVED
Expanded `VALID_VALUES` in config_appliances.py, config_faucets.py, config_fittings.py, config_generic.py to cover more attributes. Awaiting Unilog's official LOV file.

---

## Key Files to Know

| File | What It Does |
|------|-------------|
| `files/pipeline.py` | Core 10-step pipeline — **this is where most changes go** |
| `files/models.py` | Data model — Product, Attribute, Evidence, etc. |
| `files/config_appliances.py` | Category config — attributes, UOM, VALID_VALUES, templates |
| `files/config_generic.py` | Generic fallback config for unrecognized categories |
| `files/config_faucets.py` | Faucet category config |
| `files/config_fittings.py` | Fittings category config |
| `files/web_evidence_provider.py` | Web scraping — 28+ manufacturer search URLs, 40+ brand domains |
| `files/evidence_provider.py` | Abstract base class only (no more hardcoded data) |
| `files/pdf_evidence_provider.py` | Generic PDF extraction for ANY MPN |
| `files/desc_extraction_provider.py` | Doc-First extraction from Part_Desc |
| `files/normalizer.py` | Paper 1 — 200+ normalization rules |
| `files/html_spec_extractor.py` | Paper 2 — 12 HTML extraction patterns, wrapper induction |
| `files/export_mapper.py` | 252-column CSV export |
| `files/column_detector.py` | Smart column detection — 100+ CSV format aliases |
| `files/eval.py` | CompositeProvider + NoMockProvider |
| `files/validate_ground_truth.py` | **PRIMARY VALIDATION** — real pipeline vs ground truth |
| `files/server.py` | FastAPI server with 20 parallel workers |
| `frontend/app.js` | Frontend SPA — 7 views |
| `frontend/styles.css` | White enterprise theme |
| `docs/DOC_MAINTENANCE_GUIDE.md` | **READ THIS** — how to keep docs updated |

---

## Rules for You

1. **NEVER MOCK** — See anti-mock directive above. Use real providers only.
2. **Never fabricate data** — if evidence not found, mark `needs_review` with 0% confidence
3. **Always update docs** — per `docs/DOC_MAINTENANCE_GUIDE.md`
4. **Validate with ground truth** — `python validate_ground_truth.py` must show improvement
5. **No e-commerce sources** — Amazon, eBay, Home Depot are forbidden
6. **Every value needs source URL** — no exceptions
7. **Commit often** — small, focused commits with clear messages
8. **Push to GitHub** — so the team can see your progress

---

## Contact

If you have questions, check the docs first. If still stuck, reach out via the team's communication channel.

**Good luck. Let's win this.**
