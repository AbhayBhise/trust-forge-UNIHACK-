**Version:** 3.0
**Date:** 2026-08-18
**Owner:** TrustForge Team
**Status:** Active
**Last Updated:** 2026-08-18

# API Contracts

All endpoints are defined in `files/server.py`. Frontend is served at `/frontend/`.

---

## POST /pipeline/process
Synchronous processing. Reads CSV, processes all rows sequentially, returns results immediately.

**Input:** `multipart/form-data`
- `file` (required): CSV with columns `Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf`

**Validation:**
- File must end with `.csv`
- All 6 required columns must be present
- Must contain at least 1 data row

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
  "csv_url": "/files/export_1234567890.csv"
}
```

**Errors:** 400 (invalid CSV, missing columns, empty file)

---

## POST /pipeline/jobs
Background processing. Creates a job, starts parallel workers, returns immediately with job_id.

**Input:** `multipart/form-data`
- `file` (required): Same CSV schema as above

**Validation:** Same as `/pipeline/process`, plus max 10,000 rows.

**Output (JSON):**
```json
{
  "job_id": "abc123",
  "total_rows": 1000,
  "status": "processing"
}
```

**Errors:** 400 (invalid CSV, missing columns, over row limit)

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
    "rate_per_sec": 0.3,
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
{"status": "processing", "completed": 500, "total": 1000, "percent": 50.0, "rate": 0.3}
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
