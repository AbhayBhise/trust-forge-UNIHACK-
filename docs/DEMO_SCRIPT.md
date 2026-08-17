# Demo Script

Target Time: < 5 minutes

| Step | Action (Expected Click) | Expected Output | Fallback | Time (s) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Intro & Architecture** | Open `categories.html` | Configuration-driven architecture explanation across Appliances, Lighting, Fasteners. | Skip to dashboard | 45 |
| **2. Dashboard Stats** | Open `index.html` (Enterprise QA & Batch stats) | 999 processed, 997 guarded, 2 verified. Deterministic Matrix shown. | Refresh browser cache | 30 |
| **3. Product Journey** | Click product `WDTS7024RZ` row -> opens Journey | Animated 7-step sequence lighting up to "Pipeline Complete". | Reload page if animation hangs | 30 |
| **4. Attribute Traceability** | Click "View Product Details" -> opens Detail | Confidence score bars, validation pass rate, and generated descriptions. | Show JSON output | 45 |
| **5. Explainability** | Click "Explain" next to `Voltage Rating` | Side-by-side view showing validation rules passed and PDF snippet. | Explain manually using `diff_data.json` | 45 |
| **6. Failure Mode** | Click "Explain" on an `unknown` attribute | Shows Confidence 0.0%, "No Evidence", and how pipeline gracefully handled it. | Show "Enterprise QA" page queue | 30 |
| **7. Live CSV Diff** | Click "Live CSV Diff" in top nav | Side-by-side expected vs. generated data with hoverable `reason` tooltips for mismatches. | Show `evaluation_report.md` | 45 |
| **8. Export Artifact** | Open `Unihack_ Delivered Output.csv` in Excel / IDE | Exactly 252 columns, UTF-8 formatted, clean data. | Show generated JSON | 30 |

Total Time: ~300 seconds (5 minutes).
