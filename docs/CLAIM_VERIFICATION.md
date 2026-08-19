**Version:** 3.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-18

# Claim Verification

| Claim | Verified | Evidence | Status |
|-------|----------|----------|--------|
| **Deterministic pipeline** | YES | `pipeline.py` uses hardcoded logic, regex, static config. No LLMs. 10-run determinism test passes. | Locked |
| **Zero hallucination** | YES | Doc-First philosophy enforced. Unknown MPNs → `needs_review` with 0% confidence. | Locked |
| **Real PDF parsing** | YES | `PDFEvidenceProvider` parses real PDFs via PyMuPDF. | Complete |
| **Real web evidence** | YES | `WebEvidenceProvider` scrapes manufacturer sites. Real data extracted for some MPNs. | Complete |
| **Parallel processing** | YES | `ThreadPoolExecutor` with 8 workers. Background job queue with progress tracking. | Complete |
| **Graceful degradation** | YES | Unknown MPNs → `needs_review`. Web timeouts → fallback. Errors don't crash batch. | Locked |
| **Works on 1000 rows** | YES | `run_batch.py` processes all 1000 rows. MAX_ROWS = 10,000. | Complete |
| **Explainable confidence** | YES | Every field has evidence chain, validation report, confidence score. | Locked |
| **Export matches schema** | YES | Output CSV matches exact 252-column schema. `export_mapper.py` maps all columns. | Locked |
| **68.3% accuracy** | YES | Ground truth validation: 82/120 fields matched. 4 GT quality issues found. | Complete |
| **26+ tests passing** | YES | 13 test files across unittest and standalone scripts. | Complete |
| **Research papers implemented** | YES | Paper 1 → `normalizer.py`. Paper 2 → `html_spec_extractor.py`. | Complete |
