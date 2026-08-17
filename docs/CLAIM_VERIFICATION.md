# Claim Verification

| Claim | Verified | Evidence | Action Required |
| :--- | :--- | :--- | :--- |
| **Deterministic pipeline** | YES | `pipeline.py` relies solely on hardcoded logic, static taxonomies, and regex parsing. No LLMs are used for extraction or confidence scoring. | None |
| **Real PDF parsing** | PARTIAL | `PDFEvidenceProvider` parses a local PDF, but it is currently mapped explicitly to the MPN `PDSH4816AF` and uses a fallback `HardcodedRealDataProvider` for other items. | None (Documented prototype limitation) |
| **Graceful degradation** | YES | `run_batch.py` processes 1000 rows. 997 rows fall back to `0.0` confidence and `needs_review` status because evidence is unavailable. | None |
| **Works on 1000 rows** | YES | `run_batch.py` outputs all 1000 rows, filtering missing data accurately without crashing. | None |
| **Explainable confidence** | YES | JSON outputs in `demo_output.json` contain an `evidence` array and a `validation_report` for every field. | None |
| **Export matches schema** | YES | Output CSV matches the exact 252-column schema required by Unilog. | See `EXPORT_VALIDATION.md` |
| **Scalable Evaluation** | YES | `evaluator.py` dynamically handles dynamic length inputs and produces exact matches, mismatches, and metrics. | None |


### Note on Fixture Provenance
- **The extraction pipeline is real**: PyMuPDF parses a real PDF document during execution.
- **Fixture Data**: The current Whirlpool PDF (`whirlpool_spec_sheet.pdf`) is a **synthetic reference fixture** created purely for demonstrating the complete end-to-end extraction workflow. It contains only ground-truth-supported data.
- **Future Work**: Live manufacturer PDF retrieval (web scraping/API) is outside the current project scope and is documented as future work.

