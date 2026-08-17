# Antigravity build prompt — Product Trust Engine (UniHack)

## Context
This is a working starter implementation, not a spec to build from scratch.
Five Python files already run end-to-end against two real ground-truth
appliance SKUs (Frigidaire PDSH4816AF, Whirlpool WDTS7024RZ) and produce
correct manufacturer/brand identity plus near-exact-match generated
descriptions. Attach `product_trust_engine/` (models.py, config_appliances.py,
evidence_provider.py, pipeline.py, eval.py) and
`Product-Trust-Engine-Appliances-CategoryConfig-v1.md` as the starting repo.
Read the spec doc first — it is the frozen architecture and the source of
truth for every field, template, and formula. Do not redesign it.

## Non-negotiable constraints
- **Architecture is frozen.** Deterministic pipeline, one LLM call per
  product (fact extraction from retrieved evidence text), everything else
  is plain code. No multi-agent orchestration, no LangChain/CrewAI/AutoGen,
  no per-column-range agent split.
- **Tech stack (lean, not the heavy version):**
  - Backend: Python, FastAPI (thin API layer only)
  - LLM: Anthropic API directly, no multi-provider abstraction
  - Search: Tavily, restricted to manufacturer domains only (see spec
    Section 2 sourcing hierarchy) — no fallback chain of 3 search providers
  - Parsing: BeautifulSoup for HTML, pdfplumber for PDF — nothing else
  - Storage: SQLite or flat JSON files. No PostgreSQL, no Redis, no Celery,
    no vector DB — none of these solve a problem this project actually has
  - Frontend: Vite + React + Tailwind. No Next.js, no state library beyond
    React state, add shadcn/ui only if time remains
  - No OCR, no queues, no Docker orchestration, no deployment
    infrastructure beyond "runs locally for the demo"
- **Never fabricate a value.** If confidence lands below the threshold in
  `config_appliances.py` (`NEEDS_REVIEW_THRESHOLD`), the field is withheld
  (`status: "unknown"`, `value: null`) with a reason — this already works
  in `pipeline.py`, preserve this behavior in every extension.
- **Facts before content.** All five description fields render from the
  same validated attribute set. Never let an LLM generate a description
  directly from the raw input row.

## What to build, in order
1. **Fix the known bug**: `INVOICE_DESC` template is missing a space
   between the cycles count and the material abbreviation
   (`5SST` should be `5 SST`) — see `config_appliances.py` TEMPLATES and
   `pipeline.py::_render_descriptions`.
2. **Real evidence retrieval**: implement a new `EvidenceProvider` subclass
   in `evidence_provider.py` that calls Tavily restricted to the
   manufacturer's domain (resolve domain from `Part_Manuf` via a small
   manufacturer→domain lookup you build for the appliance brands actually
   present in the 1000-row input — Frigidaire, GE, LG, KitchenAid,
   Whirlpool, Speed Queen), fetches the top manufacturer-domain result,
   parses it with BeautifulSoup/pdfplumber, and passes the extracted text
   to one Claude call that returns structured JSON matching the
   `Attribute` fields in `config_appliances.py::ATTRIBUTES`. Do not change
   the `EvidenceProvider` interface — `pipeline.py` already consumes it
   correctly.
3. **Run against all 85 appliance rows** in
   `Unihack__Sample_Dataset_-_Input.csv` (filter `Part_Manuf` contains
   "Appliance"), not just the 2 hardcoded ones. Extend `eval.py` to loop
   over all of them and report the aggregate `quality_score` distribution.
4. **252-column export mapper**: write a function that takes a `Product`
   (from `models.py`) and populates only the columns this category config
   actually covers in `Unihack__Expected_Output_-_Delivery_Format.csv`'s
   header row — leave the rest blank rather than guessing. This satisfies
   "standardized export" without inventing coverage of columns with no
   underlying data.
5. **Minimal API**: FastAPI endpoints — `POST /process` (run pipeline on
   uploaded CSV rows), `GET /products/{mpn}` (return one product's full
   JSON), `GET /products` (list with quality scores for the review queue).
6. **Frontend — build in this priority order, stop if time runs out**:
   a. Product list view with quality score, confidence, status badges
   b. **Evidence/decision-log card** (click an attribute → see value,
      evidence source + tier, checks passed/failed with reasons,
      confidence). This is the single highest-priority UI element — it is
      the whole pitch made visible. Build this before anything else visual.
   c. Aggregate dashboard (rows processed, auto-approved vs needs-review
      count, mean confidence) — only after (a) and (b) work.
7. **Evaluation report**: script or notebook comparing pipeline output
   against the 2 ground-truth rows field-by-field (already partially done
   in `eval.py`), plus aggregate stats (% required fields populated, %
   passed validation, mean confidence, character-limit compliance for
   INVOICE_DESC/MOBILE_DESC) across all 85 rows once step 3 is done.

## Explicitly out of scope — do not build these even if asked
Incremental/delta reprocessing infrastructure, persistent cross-run
evidence caching, bounding-box evidence grounding, cross-family alias/
identity resolution beyond basic MPN normalization, coverage of the full
252 columns, LOV/UOM validation against the master files (not provided —
confirmed absent from the platform's Resources page), multi-agent
orchestration, any database beyond SQLite/JSON, any deployment
infrastructure beyond running locally for the demo.

## Definition of done for the hackathon submission
- Pipeline runs on all 85 appliance rows without crashing
- At least the 2 known ground-truth rows match on manufacturer, brand,
  and the 5 description fields (within reasonable tolerance)
- Evidence/decision-log UI works for at least one product end to end
- Aggregate dashboard shows real numbers, not placeholders
- Export produces a CSV with the correct headers from the Delivery Format
  file, populated columns only, no fabricated blanks-as-guesses
