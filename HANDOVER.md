# TrustForge — Complete Project Handover

> **Last updated:** 2026-08-23 | **Branch:** `main`
> **Deadline:** 23rd August, 11:59 PM IST

---

## 0. 2026-08-23 SESSION — ANTI-MOCK AUDIT & REAL-DATA FIXES

Everything below this section was written 2026-08-21 and describes the state
*before* this session. Read this section first — it corrects several claims
below that turned out not to hold up under real testing, and explains what
actually changed today. **Do not trust the "84.8% GT accuracy" number as
representative of judged performance** — see 0.3.

### 0.1 Real violations found and fixed
- **`gemini_evidence_provider.py` had the two GT MPNs' exact spec answers
  hardcoded into the extraction prompt** (Section 6 below claims "MOCKS ARE
  PERMANENTLY BANNED" — this was a live violation of that rule). Removed.
- **`export_mapper.py` fabricated `Product Image`/`Specification Sheet`
  filenames** (`{BRAND}_{MPN}.jpg`) with no evidence they exist. Now only
  populated from a real, traced PDF URL when one was actually found.
- **`WebEvidenceProvider` silently called `http://127.0.0.1:8001/fetch`** — a
  Playwright proxy nothing in the codebase ever starts (not `server.py`, not
  `render.yaml`). Every real web fetch was failing invisibly and falling
  through to weaker evidence. `playwright_server.py` deleted; scraping is now
  in-process via `agentic_provider.AdaptiveScraperAgent`.
- **`agentic_provider.py` (DDGS search + Wayback + stealth scraping) was
  fully built but never wired into `CompositeProvider`** — it's now the
  live-search fallback tier in `eval.py`.
- **False-positive identity bug**: blind-guessing across 28 unrelated
  manufacturer domains let a "no results for '&lt;query&gt;'" page falsely
  satisfy the "MPN found on page" check, reporting a 3M product as verified
  LG data. Fixed via real brand-signal resolution (explicit field or
  description keyword) + a no-results-page guard — no more blind guessing.
- **`_infer_brand()` used naive substring matching** (`"lg" in html.lower()`)
  — Bootstrap CSS classes like `col-lg-6`/`d-lg-none` are everywhere on real
  websites, so short brand keys ("lg", "ge", "3m") false-positived constantly.
  A real Southwire cable page got misattributed to "LG Electronics" this way.
  Fixed: word-boundary matching, visible-text-only scan (not raw markup),
  and short/ambiguous keys are only trusted from the page's own title.
- **Gemini brand hallucination overriding real input data**: the pipeline
  blindly let any evidence bundle's guessed manufacturer overwrite
  `Part_Manuf` from the input row, even when Gemini invented an unrelated
  well-known brand. Now a real, non-placeholder `Part_Manuf` value wins over
  an unverified LLM guess.
- **`server.py` timeout mismatch**: `TIMEOUT_SECONDS = 8.0` predated any real
  network calls. Once scraping actually worked, every row legitimately took
  35–90s and would have been marked "failed" by the 8s timeout. Raised to
  60s; each provider now also self-limits (`MAX_TIME_PER_MPN` / circuit
  breakers) so the worst case stays bounded.
- Two dataclass crash bugs fixed (`Product()` called without required
  fields in exception-handling fallback paths — Section 5, bug #2 below).
- `config_generic.py`'s single flat 46-attribute list (spanning abrasives +
  plumbing + electrical + lumber + hardware, applied to every non-appliance
  product regardless of relevance) was split into a small base set plus
  per-subcategory sets, routed by keywords in the product's own description.
  A sanding belt no longer gets asked about Wire Gauge or Wood Species.
- Every `Attribute` now carries a `reason` field — a real per-provider trail
  (`CompositeProvider._evidence_trail`) of what was checked and what each
  source found/missed, surfaced on the Product Detail UI. "Unknown" no
  longer means "no explanation," it means "here's exactly what we checked."

### 0.2 Security/resilience hardening added
- `/files` static mount used to serve the **entire `files/` directory** —
  source code, `web_evidence_cache.json`, `gemini_cache.json`, `server.log`
  — publicly. Now scoped to a dedicated `files/exports/` directory that only
  ever contains generated CSVs.
- CSV/Excel formula-injection neutralization on export (`export_mapper.py`)
  — a cell value starting with `=`/`+`/`-`/`@` (possible via scraped/LLM
  text) is prefixed to render as literal text, not a live formula.
- SSRF guard in `agentic_provider.py` — refuses to fetch any URL that isn't
  plain http(s) to a public host (blocks localhost, private ranges, link-
  local/cloud-metadata addresses) before making a request to a
  search-result-supplied URL.
- Basic per-IP rate limiting (10 req/60s) and a 25MB upload cap on the
  processing endpoints.
- Marketplace/distributor domain exclusion list in `agentic_provider.py` —
  the solution guide explicitly forbids sourcing from marketplaces/
  distributors; a raw web search for an MPN routinely surfaces exactly
  those, so results are filtered before ever being fetched.

### 0.3 On the "84.8% GT accuracy" number
This number **did not change at all** after removing the hardcoded Gemini
answers, which was surprising until traced: `validate_ground_truth.py` (and
`eval.py:run()`, Section 5 bug #1) only ever test the 2 MPNs that are
*already in* the official GT CSV, and `GroundTruthSeedProvider` intercepts
those 2 MPNs first, before Web/Agentic/PDF/Gemini/Description ever run —
it just reads the answer back out of the same file that defines the
"ground truth." **The judges' evaluation dataset will not contain these 2
MPNs**, so this metric measures nothing about real extraction capability.
Real-world behavior looks like the diverse smoke tests in this session
(abrasives/electrical/hardware/lumber rows never seen in GT) — correct
identity resolution most of the time post-fixes, partial attribute coverage
depending on whether a real manufacturer page/PDF/LLM knowledge exists for
that specific MPN, and honest `needs_review`/`unknown` with a stated reason
otherwise. If you want a real accuracy number to cite, measure against
non-GT rows with manually-verified spot checks — not this script.

### 0.4 Known remaining gaps (not fixed this session, be aware of these)
- Controlled vocabulary compliance: the solution guide requires brand names
  and attribute values to come from Unilog's ~27,000-row approved brand list
  and ~161,000-row LOV file. Those files were never provided to us — our
  `config_generic.py` LOV sets are a best-effort approximation, not the real
  list. Don't claim full LOV compliance in the demo.
- Full-batch throughput: with real scraping/LLM calls, ~1000 rows at 20
  workers realistically takes tens of minutes, not seconds. The background
  job + polling UI handles this, but budget real wait time before a live demo.
- Gemini quota: the configured key was rate-limited on nearly every call
  during testing. A circuit breaker now stops wasting time retrying against
  it, but that also means Gemini contributes less when quota is exhausted —
  check quota/billing before relying on it in the demo.
- `eval.py:run()` still has the circular-evaluation bug described in Section
  5, bug #1 — it wasn't touched this session since it's a dev script, not
  the production path (`server.py`), but don't cite its output either.

---

## 1. PROJECT OVERVIEW

**TrustForge** is an AI-powered product intelligence engine for the **UniHack 2026** hackathon with **Unilog** (B2B product data company). It transforms sparse distributor CSV inputs (6 columns, 1000 rows) into 252-column commerce-ready catalogs.

**Repo:** `https://github.com/AbhayBhise/trust-forge-UNIHACK-.git`

### Core Philosophy
- **Doc-First:** Every value extracted from real sources, never fabricated
- **Zero Hallucination:** Unknown data marked `needs_review` with 0% confidence, never guessed
- **Evidence Traceability:** Every attribute has source URL, tier, and timestamp
- **Deterministic:** Same input always produces identical output (no LLM variance)

### Evaluation Weights (from Ramachandra Raja, Unilog VP)
| Weight | Category | What judges look for |
|--------|----------|---------------------|
| **40%** | Output Accuracy | Correct attribute extraction, proper UOM, source URLs |
| **30%** | Architecture | Code quality, modularity, research paper implementation |
| **30%** | Demo | Live CSV upload, real-time activity feed, explainability |

---

## 2. CURRENT STATE — WHAT WORKS

### Last 10 Commits (newest first)
```
e14e63f Expand desc extraction: 20+ new patterns, 40+ generic attributes, MPN stripping
04211af fix: activity tracker not emitting events to frontend
9252bc2 feat: real-time pipeline activity feed in UI
37ee4a7 v1.1: Remove all mocking, improve accuracy to 85%+
656cbf0 feat: implement high-performance persistent playwright server
7632744 fix: MPN-to-manufacturer mapping and validate_ground_truth
9f00ec1 fix: server restart with new CompositeProvider
3a5846c feat: universal attribute extraction for all 1000 rows
fe7101d feat: push GT accuracy from 77% to 84.8% with zero mismatches
5be261b feat: add real ground truth validation engine and anti-mock directive
```

### Core Pipeline (`files/pipeline.py` - 639 lines)
10-step deterministic pipeline:
1. **Deduplicate** rows (normalize MPN to alphanumeric key)
2. **Resolve identity** (brand placeholders to real brand names)
3. **Fetch evidence** (CompositeProvider: GT Seed -> Web -> PDF -> Description)
4. **Extract attributes** (from evidence bundle facts dict)
5. **Normalize values** (Paper 1 - `normalizer.py`, 200+ rules)
6. **Cross-validate** evidence consistency
7. **Validate** (enum checks, UOM enforcement, required fields)
8. **Score confidence** (multi-factor heuristic: tier x consistency x completion)
9. **Generate descriptions** (6 deterministic templates with char limits)
10. **Compute quality score** (completeness x pass_rate x mean_confidence)

### Evidence System (ALL REAL PROVIDERS, NO MOCKING)
| Provider | File | Lines | What it does |
|----------|------|-------|-------------|
| `GroundTruthSeedProvider` | `gt_seed_provider.py` | 127 | Reads verified GT CSV as Tier-5 evidence |
| `WebEvidenceProvider` | `web_evidence_provider.py` | 762 | Scrapes 28+ manufacturer search URLs, 40+ brand domains |
| `PDFEvidenceProvider` | `pdf_evidence_provider.py` | 290 | Generic PDF extraction via PyMuPDF for ANY MPN |
| `DescriptionExtractionProvider` | `desc_extraction_provider.py` | 457 | Doc-First extraction from Part_Desc - 20+ patterns |
| `CompositeProvider` | `eval.py` | 252 | Chains: GT Seed -> Web -> PDF -> Description |

### Category Configs
| Config | File | Attributes | LOV Values |
|--------|------|-----------|------------|
| Appliances | `config_appliances.py` | 50 attributes | Voltage, Amperage, Mounting, Material, Color, Wash Cycles |
| Faucets | `config_faucets.py` | ~15 attributes | Faucet Type, Finish, Flow Rate, Handles |
| Fittings | `config_fittings.py` | ~15 attributes | Fitting Type, Connection Type, Pipe Size, Pressure |
| **Generic** | `config_generic.py` | **40+ attributes** | Material (19 types), Color (16 options), Size, Grit, etc. |

### Description Extraction Patterns (desc_extraction_provider.py)
**20+ extraction patterns** covering:
- **Dimensions:** Size, Length (fractional inch, WxH notation, foot-length)
- **Abrasives:** Grit grade (P80, P120, etc.), abrasive material (Silicon Carbide, Aluminum Oxide, etc.)
- **Plumbing:** Fitting type (Elbow, Tee, Coupling), Connection type (NPT, FPT, Solder), Pipe size, Flow rate, Max pressure
- **Electrical:** Wire gauge (AWG), Voltage, Amperage, Wattage, Number of conductors
- **Hardware:** Thread size, Head type, Drive type
- **Lumber:** Wood species, Grade, Treatment
- **Tools:** Diameter, Thickness, Arbor size, Max RPM
- **Universal:** Material (19 types), Color (16 options), Mounting, Edge type, Profile, Series

**MPN stripping:** Before pattern matching, the MPN is removed from the description text to prevent false positives.

### Server (`files/server.py` - 417 lines)
FastAPI with endpoints:
- `POST /pipeline/process` - sync processing
- `POST /pipeline/jobs` - background job queue
- `GET /pipeline/jobs/{id}` - progress polling (returns events array)
- `GET /pipeline/jobs/{id}/stream` - SSE streaming
- `GET /health` - health check
- `GET /debug/tracker` - activity tracker debug

Parallel processing: **20 workers** via ThreadPoolExecutor.

### Frontend (`frontend/` - 4 files)
White enterprise-themed SPA with 7 views:
- **Dashboard** - KPIs, product table with pagination
- **Process CSV** - drag-drop upload, column detection, real-time activity feed with animated events
- **Ground Truth Diff** - field-by-field comparison with accuracy
- **QA Metrics** - system guarantees and validation stats
- **Pipeline Journey** - animated step-by-step visualization
- **Product Detail** - attribute grid with evidence links and View Source buttons
- **Explainability** - detailed evidence source breakdown per attribute

### Activity Tracker (`files/activity_tracker.py`)
Thread-safe event capture. Events flow: pipeline -> tracker -> SSE -> frontend.
Instrumented in: `pipeline.py`, `eval.py`, `web_evidence_provider.py`, `pdf_evidence_provider.py`, `desc_extraction_provider.py`.
Bug fixed: worker thread crash silently prevented events (commit `04211af`).

### Tests
32 core tests passing across test files: `test_models.py`, `test_column_detector.py`, `test_mapper.py`, `test_new_modules.py`, `test_pipeline.py`, `test_config_appliances.py`, `test_validation.py`, `test_zero_evidence.py`, `test_robustness.py`.

Run: `cd files && python -m pytest -v`

### Research Papers Implemented
- **Paper 1** (More, WalmartLabs 2016): `normalizer.py` - 200+ normalization rules, UOM enforcement
- **Paper 2** (Gangadhar and Kulkarni 2022): `html_spec_extractor.py` - 12 HTML extraction patterns, wrapper induction

---

## 3. WHAT THE HACKATHON EXPECTS

### From Ramachandra Raja, VP Content Services at Unilog (live session 2026-08-18)

### Input Data
- **Manufacturer Part Number** (Column A) - the core identifier
- **Manufacturer Name** (Column F) - who makes it
- Additional: E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf
- Our input CSV: `Unihack_ Sample Dataset - Input.csv` (1000 rows, 6 columns)

### Output Requirements (252 columns)
1. **Classify into taxonomy** - Unilog has ~14,000 leaf-level categories
2. **Populate attributes** - Each category has 10-40+ predefined attributes
3. **UOM captured separately** - Value in one column, unit in next (e.g., 120 | V)
4. **LOV validation** - Check values against List of Values
5. **6 description types** with strict character limits:
   - MOBILE_DESC (80 chars), INVOICE_DESC (40 chars), SHORT_DESC (200 chars)
   - LONG_DESC1 (800 chars), RETAIL_DESC (500 chars), MATCH_DESC (120 chars)
6. **MARKETING_DESCRIPTION** - as-is from manufacturer website
7. **ITEM_FEATURES_1..20** - from manufacturer website only
8. **Digital assets** - images, PDFs, warranty, tech specs - manufacturer website ONLY
9. **EAN/UPC** - if available in source
10. **Warranty, list price, packaging** (length/width/height)

### Source Rules (CRITICAL)
| Rule | Detail |
|------|--------|
| Primary source | **Manufacturer's official website ONLY** |
| **FORBIDDEN** | **Amazon, eBay, any e-commerce/shopping sites** |
| If manufacturer site dead | Reputed third-party sources (NOT e-commerce) |
| Every value needs | **Source URL** for validation |
| If from PDF | Must provide PDF or link to it |

### Submission Rules
- **Dynamic dataset upload** - evaluators WILL upload their own data
- **No hardcoded/mocked outputs**
- **No static output screens**
- **No features that only work in demo**
- Must test with data not used as primary demo
- Must run complete workflow end-to-end without failures
- **Live prototype link** required

---

## 4. COMPARISON: WHAT WE HAVE vs WHAT WE NEED

### What we deliver well (Architecture 30% - STRONG)
- Clean 10-step pipeline, modular configs, research paper implementations
- Activity tracker, real-time frontend, evidence traceability
- No mocking, no hallucination, deterministic output
- Smart column detection (accepts ANY CSV format)

### What we deliver partially (Accuracy 40% - NEEDS WORK)

**GT products (2 MPNs with ground truth): 84.8% accuracy**
- Identity fields: MATCH (manufacturer, brand, classpath)
- Description templates: Partially match (wording differs)
- Attributes: Some values match, some are off

**Non-GT products (998 MPNs): 1-4 attributes from description extraction only**
- Generic category detection works
- Description extraction provides: Size, Material, Grit, Quantity, Color
- Missing: Item features, marketing description, digital assets, EAN/UPC

### What we are MISSING (Accuracy gap)

| Requirement | Status | Gap |
|-------------|--------|-----|
| 252-column CSV export | Works but sparse for non-GT | Many columns empty for non-GT products |
| Marketing Description | Extracted from web when available | Most sites block scraping |
| Item Features (1-20) | Not populated | Need manufacturer page extraction |
| Digital Assets (images, PDFs) | Not populated | Need manufacturer page scraping |
| EAN/UPC | Not extracted | Need to parse from web/PDF sources |
| Warranty | Not extracted | Need to parse from web/PDF sources |
| LOV Validation | Partial (local vocab only) | Unilog's official LOV file not provided |
| Taxonomy Classification | Keyword-based (15+ types) | Need mapping to Unilog's 14,000 categories |
| PART_NUMBER, Dept, Class, Fine | Not populated from input | These come from Unilog's internal system |

---

## 5. KNOWN BUGS AND FLAWS

### Critical Bugs
1. **`eval.py` circular evaluation** (line 194-195): `run()` filters rows to only MPNs present in GT seed DB. This means accuracy is measured ONLY on products whose answers are already in the ground truth file. This inflates accuracy and does NOT test real extraction on unknown products.

2. **`server.py` fallback crash** (lines 118, 166): Fallback paths construct `Product(mfg_part_num=mpn)` and `Product()` but `models.Product` requires both `mfg_part_num` and `part_desc` with no defaults. This causes `TypeError` inside exception handlers, potentially killing background batch threads so jobs never complete.

3. **`pipeline.py` identity "verified" too easily**: Identity is marked "verified" whenever ANY evidence bundle returns, even Tier-2 description-only evidence. This is misleading.

### Moderate Bugs
4. **`pipeline.py` category `getattr` always returns Unknown**: `product._category` is read via `getattr` (lines 126, 294) but **never set anywhere**, so those branches are always false.

5. **`pipeline.py` low-confidence values silently nulled**: At line 452, `attr.value = None` silently drops values below confidence threshold without logging.

6. **`server.py` `/files` static mount exposes everything**: The `/files` static mount exposes the entire `files/` directory including logs, cache JSON, and generated exports.

7. **`server.py` shared provider across threads**: Single `CompositeProvider` shared across 20 threads with no lock protection. Provider internals (throttle timestamps, caches) may race.

8. **`server.py` blocking sleep in async SSE**: Uses `time.sleep()` inside async route, blocking the event loop.

### Design Issues
9. **`MPN_MANUFACTURER_MAP` hardcoded** (pipeline.py lines 30-36): Maps only 5 MPN prefixes to brands. Works for GT products but not the 1000-row dataset.

10. **Description extraction only gets 1-4 attrs per row**: The dataset descriptions are terse (1-2 lines). Without web scraping success, non-GT products have very sparse output.

11. **`NoMockProvider` does not use `fetch_with_row`**: Its `fetch()` method (line 162) does not pass row context, so description extraction never runs in that code path.

12. **`eval.py` double processing**: Products are built twice (once for printing, once at line 236 for export) causing duplicate tracker events.

---

## 6. STRICT ANTI-MOCK DIRECTIVE

**MOCKS ARE PERMANENTLY BANNED FROM THIS CODEBASE.**

### What Counts as Mocking
- `HardcodedRealDataProvider` - **DELETED.** Was a hardcoded cache for 2 MPNs.
- Hardcoded test data that simulates pipeline output
- Unit tests that use mock providers to make tests pass without real extraction
- Any function that returns pre-built results instead of extracting from real sources
- Any test that does not run against actual files or actual HTTP endpoints

### What You Must Use Instead
- `WebEvidenceProvider` - scrapes real manufacturer websites (NOT e-commerce)
- `PDFEvidenceProvider` - extracts from ANY manufacturer PDF (generic)
- `DescriptionExtractionProvider` - Doc-First extraction from Part_Desc
- `CompositeProvider` - chains GT Seed -> Web -> PDF -> Description

### How to Validate
1. Run `cd files && python validate_ground_truth.py`
2. It compares pipeline output against `Unihack_ Expected Output - Delivery Format.csv`
3. Outputs `ground_truth_accuracy_report.json`
4. **This is the score we show to judges.**

---

## 7. ABSOLUTE RULES FOR CONTINUING DEVELOPMENT

### NEVER DO THESE
1. **Never add hardcoded provider data** - No MPN-to-value caches, no hardcoded product specs
2. **Never remove features or attributes** - If a config defines it, the pipeline must try to extract it
3. **Never fabricate data** - If evidence not found, mark `needs_review` with 0% confidence
4. **Never use e-commerce sources** - Amazon, eBay, Home Depot, Lowe's are FORBIDDEN
5. **Never skip source URLs** - Every attribute value must have a traceable `Evidence.source_url`
6. **Never delete tests** - Fix them, do not remove them
7. **Never modify `Unihack_ Expected Output - Delivery Format.csv`** - This is the ground truth
8. **Never bypass the activity tracker** - All pipeline steps must emit tracker events

### ALWAYS DO THESE
1. **Always update docs** - per `docs/DOC_MAINTENANCE_GUIDE.md`
2. **Always validate with ground truth** - `python validate_ground_truth.py` must show improvement
3. **Always emit tracker events** - Use `tracker.emit()` for every pipeline step
4. **Always use `fetch_from_row()`** - Description extraction needs row context (Part_Desc)
5. **Always commit often** - Small, focused commits with clear messages
6. **Always push to GitHub** - So the team can see progress
7. **Always add new attributes to config_generic.py** - When adding extraction patterns
8. **Always handle missing data gracefully** - Never crash, always degrade to `needs_review`

### Logging Requirements
- Every provider call must emit tracker events (step, provider, action, detail, icon, status)
- Pipeline steps must log: category detection, attribute population, normalization, validation, confidence scoring
- Frontend must show real-time events in the activity feed
- All errors must be caught and logged, never silently swallowed

---

## 8. HOW TO RUN

### Setup
```bash
git clone https://github.com/AbhayBhise/trust-forge-UNIHACK-.git
cd trust-forge-UNIHACK-
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### Start Server
```bash
cd files
python server.py
# Open http://127.0.0.1:8000/frontend/
```

### Run Tests
```bash
cd files
python -m pytest test_models.py test_column_detector.py test_mapper.py test_new_modules.py test_pipeline.py test_config_appliances.py test_validation.py test_zero_evidence.py test_robustness.py -v
```
Note: Some test files (`test_determinism.py`, `test_pw.py`, `test_web_*.py`) hang on network calls. Run them individually with shorter timeouts if needed.

### Validate Against Ground Truth
```bash
cd files
python validate_ground_truth.py
```

---

## 9. KEY FILES REFERENCE

### Core Pipeline
| File | Lines | Purpose |
|------|-------|---------|
| `files/pipeline.py` | 639 | Core 10-step pipeline - most changes go here |
| `files/models.py` | 104 | Data model: Product, Attribute, Evidence, Identity |
| `files/eval.py` | 252 | CompositeProvider + evaluation runner |
| `files/server.py` | 417 | FastAPI server with 20 parallel workers |
| `files/activity_tracker.py` | 93 | Thread-safe event tracking for UI feed |

### Evidence Providers
| File | Lines | Purpose |
|------|-------|---------|
| `files/evidence_provider.py` | 23 | Abstract base class only |
| `files/web_evidence_provider.py` | 762 | Web scraping: 28 URLs, 40+ brands, persistent cache |
| `files/pdf_evidence_provider.py` | 290 | Generic PDF extraction via PyMuPDF |
| `files/desc_extraction_provider.py` | 457 | Doc-First extraction: 20+ patterns |
| `files/gt_seed_provider.py` | 127 | Ground truth CSV as Tier-5 evidence |
| `files/html_spec_extractor.py` | 398 | Paper 2: HTML spec block extraction |

### Category Configs
| File | Lines | Attributes |
|------|-------|-----------|
| `files/config_appliances.py` | 145 | 50 attributes (dishwashers, etc.) |
| `files/config_faucets.py` | 95 | ~15 attributes |
| `files/config_fittings.py` | 95 | ~15 attributes |
| `files/config_generic.py` | 164 | **40+ attributes** (abrasives, plumbing, electrical, lumber, hardware, tools) |

### Data Processing
| File | Lines | Purpose |
|------|-------|---------|
| `files/normalizer.py` | 392 | Paper 1: 200+ normalization rules |
| `files/export_mapper.py` | 173 | 252-column CSV export mapping |
| `files/column_detector.py` | 264 | Smart column detection: 100+ CSV format aliases |

### Frontend
| File | Lines | Purpose |
|------|-------|---------|
| `frontend/app.js` | 789 | SPA: 7 views, activity feed, polling |
| `frontend/styles.css` | 798 | White enterprise theme |
| `frontend/index.html` | 64 | Main page shell |
| `frontend/categories.html` | 69 | Config-driven categories page |

### Data Files
| File | Purpose |
|------|---------|
| `Unihack_ Sample Dataset - Input.csv` | Input: 1000 rows, 6 columns |
| `Unihack_ Expected Output - Delivery Format.csv` | Ground truth: 252 columns, 2 rows |
| `Unihack_ Delivered Output.csv` | Our delivered output |

### Docs (in `docs/`)
| File | Purpose |
|------|---------|
| `DOC_MAINTENANCE_GUIDE.md` | How to keep docs updated when code changes |
| `ARCHITECTURE.md` | System architecture |
| `API_CONTRACT.md` | API endpoint documentation |
| `DATA_MODEL.md` | Product/Attribute/Evidence model |
| `DEMO_SCRIPT.md` | Demo presentation script |
| `KNOWN_LIMITATIONS.md` | Design limitations and trade-offs |
| `TECHNICAL_DEBT.md` | Technical debt log |

---

## 10. PRIORITY NEXT STEPS TO WIN

### Priority 1: Fix Critical Bugs (1-2 hours)
1. Fix `server.py` fallback crash - add `part_desc=""` default to Product constructor or fix fallback paths
2. Fix `eval.py` circular evaluation - process ALL 1000 rows, not just GT-known MPNs
3. Fix `pipeline.py` category `getattr` - actually set `product._category` from the detection logic
4. Fix `NoMockProvider.fetch()` - use `fetch_with_row()` so description extraction works

### Priority 2: Improve Accuracy on Non-GT Products (2-4 hours)
5. Web scraping success rate is low (most sites block). Consider adding Playwright browser automation for JS-rendered pages
6. Expand `web_evidence_provider.py` brand domain mappings for the 1000-row dataset brands
7. Add more extraction patterns to `desc_extraction_provider.py` for brands in the dataset (Milwaukee, Diablo, 3M, Mirka, etc.)
8. Fix confidence scoring - Tier 2 (description) should not boost to 90%+; cap at 0.70

### Priority 3: Output Completeness (1-2 hours)
9. Ensure 252-column export populates ALL fields we can extract (PART_NUMBER, Dept, Class, Fine from taxonomy)
10. Map description extraction categories to Unilog taxonomy (Abrasives > Sanding > Discs, etc.)
11. Populate ITEM_FEATURES from web scraping when available
12. Populate MARKETING_DESCRIPTION from web scraping when available

### Priority 4: Demo Polish (1 hour)
13. Test full flow: upload CSV -> process -> view dashboard -> view product detail -> view explainability
14. Ensure activity feed shows real-time events during processing
15. Prepare demo script per `docs/DEMO_SCRIPT.md`

### Priority 5: Submission (30 minutes)
16. Final test run on the full 1000-row dataset
17. Verify all tests pass
18. Push final commit
19. Fill out submission form with live prototype link

---

## 11. IMPORTANT DATA STRUCTURES

### Evidence Bundle (returned by providers)
```python
{
    "_manufacturer_name": "Rheem Manufacturing",
    "_brand_name": "FRIGIDAIRE",
    "_series": "Professional Series",
    "source_url": "https://www.frigidaire.com/...",
    "source_tier": 5,
    "_category": "Appliances",
    "_product_name": "Dishwasher SS",
    "facts": {
        "Voltage Rating": ("120", "V", Evidence(...)),
        "Material": ("Stainless Steel", None, Evidence(...)),
        "Mounting Type": ("Leg", None, Evidence(...)),
        # ... more attributes
    }
}
```

### Product Model (pipeline.py output)
```python
Product(
    mfg_part_num="PDSH4816AF",
    part_desc="PDSH4816AF Dishwasher SS",
    manufacturer_name="Rheem Manufacturing",
    brand_name="FRIGIDAIRE",
    classpath="Appliances > Kitchen > Dishwashers",
    identity=Identity(status="verified"),
    attributes=[Attribute(attribute="Voltage Rating", value="120", uom="V", confidence=100.0, ...)],
    descriptions={"MOBILE_DESC": "...", "SHORT_DESC": "...", ...},
    quality_score=QualityScore(completeness=0.85, mean_confidence=0.92, ...)
)
```

### Tracker Event (activity feed)
```python
tracker.emit(
    mpn="PDSH4816AF",
    step="evidence_retrieval",      # pipeline step
    provider="WebEvidenceProvider",  # which provider
    action="searching",             # what action
    detail="Searching for PDSH4816AF...",
    icon="search",                  # UI icon
    status="running"                # running/success/fail/skip
)
```

---

## 12. INPUT DATASET ANALYSIS

The 1000-row dataset spans these product categories:
- **Abrasives & Sanding** (~200 rows): Sanding belts, discs, films (3M, Mirka, Diablo)
- **Cutting & Grinding** (~100 rows): Cut-off discs, grinding wheels (Milwaukee, Diablo)
- **Decking & Railing** (~200 rows): Composite decking, rail kits (Trex, Azek)
- **Plumbing** (~50 rows): Fittings, valves (Matco-Norca)
- **Electrical** (~50 rows): Wire, cable (Southwire)
- **Hardware & Fasteners** (~100 rows): Screws, bolts, nails
- **Tools** (~50 rows): Hand tools, power tool accessories
- **General Hardware** (~250 rows): Lighting, doors, windows, miscellaneous

Most descriptions are terse (1-2 lines): `MPN Brand Size - Product Type Pack/Qty`
Only 2 MPNs have ground truth data: PDSH4816AF (Frigidaire dishwasher), WDTS7024RZ (Whirlpool dishwasher)

---

**Good luck. Read this document carefully. Ask questions before making changes. Let's win this.**
