**Version:** 4.0
**Date:** 2026-08-19
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-19

# API Contracts

All endpoints are defined in `files/server.py`. Frontend is served at `/frontend/`.

**Key Change:** No hardcoded schema required. System auto-detects columns from ANY CSV format via smart column detection.

---

## POST /pipeline/process
Synchronous processing. Reads CSV, processes all rows sequentially, returns results immediately.

**Input:** `multipart/form-data`
- `file` (required): CSV with ANY column names (auto-detected)

**Smart Column Detection:**
The system automatically detects and maps columns using:
1. Exact aliases (e.g., `Mfg_Part_Num`, `MPN`, `Part_Number` → Mfg_Part_Num)
2. Pattern matching (e.g., columns containing "manufacturer" → Part_Manuf)
3. Fuzzy matching (60% similarity threshold for remaining columns)

**Validation:**
- File must end with `.csv`
- Must contain at least 1 data row
- Must have a detectable Part Number/MPN column

**Output (JSON):**
```json
{
  "products": [
    {
      "mfg_part_num": "PDSH4816AF",
      "part_desc": "...",
      "identity": {"status": "verified", "matched_on": "manufacturer_part_number"},
      "manufacturer_name": "...",
      "brand_name": "...",
      "classpath": "Built-In Dishwashers",
      "classpath_confidence": 0.95,
      "attributes": [...],
      "quality_score": {...},
      "descriptions": {...}
    }
  ],
  "csv_url": "/files/export_1234567890.csv",
  "column_map": {
    "Mfg_Part_Num": "MPN",
    "Part_Desc": "Description",
    "E1_Brand": "Brand",
    "Part_Manuf": "Manufacturer"
  },
  "warnings": ["Detected columns: {...}"]
}
```

**Errors:** 400 (invalid CSV, no MPN column detected, empty file)

---

## POST /pipeline/jobs
Background processing. Creates a job, starts parallel workers, returns immediately with job_id.

**Input:** `multipart/form-data`
- `file` (required): CSV with ANY column names (auto-detected)

**Validation:** Same as `/pipeline/process`, plus max 10,000 rows.

**Output (JSON):**
```json
{
  "job_id": "abc123",
  "total_rows": 1000,
  "status": "processing",
  "column_map": {
    "Mfg_Part_Num": "MPN",
    "Part_Desc": "Description",
    "E1_Brand": "Brand",
    "Part_Manuf": "Manufacturer"
  },
  "warnings": ["Not detected: Unilog_Brand, DIB_Brand"]
}
```

**Errors:** 400 (invalid CSV, no MPN column detected, over row limit)

---

## GET /pipeline/jobs/{job_id}
Polls job progress. Returns progress stats and results (when complete).

**Output (JSON):**
```json
{
  "id": "abc123",
  "status": "completed",
  "progress": {
    "total": 1000,
    "completed": 1000,
    "verified": 98,
    "needs_review": 902,
    "failed": 0,
    "percent": 100.0,
    "rate_per_sec": 0.5,
    "eta_seconds": 0.0
  },
  "csv_url": "/files/export_1234567890.csv",
  "products": [...]
}
```

Note: `products` is `null` while status is `"processing"`, populated when `"completed"`.

**Errors:** 404 (job not found)

---

## GET /pipeline/jobs/{job_id}/stream
Server-Sent Events stream for real-time progress updates.

**Events (each is a `data:` line with JSON):**
```json
{"status": "processing", "completed": 500, "total": 1000, "percent": 50.0, "rate": 0.5}
```

Stream ends when `status` is `"completed"`.

**Errors:** Returns `{"error": "Job not found"}` if job_id invalid.

---

## GET /health
Health check.

**Output (JSON):**
```json
{"status": "ok", "version": "1.0.0"}
```

---

## Static Mounts

| Mount | Directory | URL |
|-------|-----------|-----|
| `/frontend` | `frontend/` | `http://127.0.0.1:8000/frontend/` |
| `/files` | `files/` | `http://127.0.0.1:8000/files/demo_output.json` |

---

## Smart Column Detection Details

The `column_detector.py` module maps any CSV column name to our internal schema:

| Internal Field | Example Input Columns |
|----------------|----------------------|
| Mfg_Part_Num | MPN, Part_Number, model_number, Mfg_Part_Num, Part_Num |
| Part_Manuf | Manufacturer, MFR, Vendor, Supplier, Part_Manuf |
| E1_Brand | Brand, Brand_Name, E1_Brand, Brand_Code |
| Part_Desc | Description, Product_Description, Part_Desc, Short_Description |
| Unilog_Brand | Unilog_Brand, Unilog_Brand_Name |
| DIB_Brand | DIB_Brand, DIB_Brand_Name |
| Classpath | Classpath, Category, Taxonomy, Class |
| SKU | SKU, SKU_Number, Stock_Num |

**Detection Passes:**
1. Exact aliases (highest confidence)
2. Pattern matching (regex for common naming conventions)
3. Fuzzy matching (SequenceMatcher, 60% threshold)
