**Version:** 2.0  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Active  
**Last Updated:** 2026-08-17

# Demo Script

Target Time: < 5 minutes

| Step | Action | Expected Output | Fallback | Time |
|------|--------|-----------------|----------|------|
| **1. Architecture** | Open `categories.html` | Configuration-driven architecture explanation. | Skip to dashboard | 30s |
| **2. Dashboard Stats** | Open `index.html` | KPI cards showing verified/needs_review counts, pipeline health. | Refresh browser | 30s |
| **3. Upload CSV** | Drag-drop input CSV | Progress bar with real-time updates (rows/sec, ETA, verified/needs_review counts). | Show batch results | 60s |
| **4. Product Journey** | Click product row → Journey view | Animated pipeline steps: Identity → Evidence → Extract → Validate → Score → Describe → Export. | Show JSON output | 45s |
| **5. Attribute Details** | Click "View Product Details" | Confidence bars, validation pass rate, evidence sources, generated descriptions. | Show raw data | 45s |
| **6. Explainability** | Click "Explain" on attribute | Evidence chain, validation rules passed, source URLs, confidence breakdown. | Manual explanation | 45s |
| **7. Ground Truth Diff** | Click "Ground Truth" tab | Side-by-side expected vs. generated with color-coded diffs and reason tooltips. | Show evaluation report | 45s |
| **8. QA Metrics** | Click "QA" tab | 68.3% accuracy, GT quality issues, validation pass rates, determinism verification. | Show test results | 30s |
| **9. Export** | Open output CSV | Exactly 252 columns, UTF-8 formatted, clean data. | Show JSON output | 30s |

Total Time: ~360 seconds (6 minutes).

## Key Demo Points

1. **Zero Hallucination**: Unknown MPNs get `needs_review` with 0% confidence — no fabricated data.
2. **Evidence Traceability**: Every attribute has a source URL, tier, and retrieval timestamp.
3. **Parallel Processing**: Upload 1000 rows, see real-time progress with ETA.
4. **Graceful Degradation**: Web scraping failures don't crash the system.
5. **Research Papers**: Paper 1 (Normalizer) and Paper 2 (HTML Spec Extractor) are real implementations.

## Backup Demo (If Live Fails)

1. Show pre-generated `demo_output.json` with 10 products
2. Walk through pipeline journey for WDTS7024RZ (known MPN)
3. Show validation report in `validate_ground_truth.py` output
4. Show 252-column export in Excel
