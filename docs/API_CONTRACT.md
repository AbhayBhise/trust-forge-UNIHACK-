**Version:** 2.0  
**Date:** 2026-08-17  
**Owner:** TrustForge Team  
**Status:** Active  
**Last Updated:** 2026-08-17

# API Contracts

## POST /pipeline/process
Synchronous processing for small datasets (up to 500 rows).

**Input (multipart/form-data):**
- `file`: CSV with columns: `Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf`
- `category` (optional): Product category (default: `appliances`)
- `max_rows` (optional): Max rows to process (default: 500)

**Output (JSON):**
```json
{
  "results": [
    {
      "mpn": "PDSH4816AF",
      "confidence": 0.76,
      "status": "verified",
      "source": "hardcoded",
      "evidence_count": 15,
      "validation_pass_rate": 0.85
    }
  ],
  "summary": {
    "total": 500,
    "verified": 425,
    "needs_review": 75,
    "failed": 0
  }
}
```

---

## POST /pipeline/jobs
Background processing for large datasets (no hard limit). Returns immediately with job ID.

**Input (multipart/form-data):**
- `file`: CSV file
- `category` (optional): Default `appliances`
- `max_workers` (optional): Parallel workers (default: 8)

**Output (JSON):**
```json
{
  "job_id": "abc123",
  "status": "processing",
  "total_rows": 1000,
  "progress_url": "/pipeline/jobs/abc123",
  "stream_url": "/pipeline/jobs/abc123/stream"
}
```

---

## GET /pipeline/jobs/{job_id}
Polls job progress.

**Output (JSON):**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "total": 1000,
  "processed": 1000,
  "verified": 680,
  "needs_review": 320,
  "failed": 0,
  "percent": 100.0,
  "rate": 0.3,
  "elapsed": 3165,
  "eta": 0,
  "avg_confidence": 0.72,
  "validation_pass_rate": 0.85,
  "results": [...]
}
```

---

## GET /pipeline/jobs/{job_id}/stream
Server-Sent Events (SSE) streaming for real-time progress.

**Events:**
```
data: {"percent": 50.0, "verified": 340, "needs_review": 160, "rate": 0.3, "eta": 1500}
data: {"percent": 100.0, "verified": 680, "needs_review": 320, "rate": 0.3, "eta": 0}
event: complete
data: {"job_id": "abc123", "status": "completed"}
```

---

## GET /product/{id}
Retrieves the complete internal Product model for a specific MPN.

**Input:** Path parameter `id` (Mfg_Part_Num)
**Output (JSON):** Serialized `Product` object
**Errors:** 404 Not Found

---

## GET /decision-log/{id}
Retrieves validation reports and evidence chains for a product.

**Input:** Path parameter `id`
**Output (JSON):** List of Attribute objects with `attribute`, `evidence`, `checks`, `validation_report`
**Errors:** 404 Not Found

---

## GET /quality-score/{id}
Retrieves aggregate quality metrics for a product.

**Output (JSON):**
```json
{
  "completeness": 1.0,
  "validation_pass_rate": 0.85,
  "mean_confidence": 0.76,
  "evidence_coverage": 0.90
}
```
**Errors:** 404 Not Found

---

## GET /categories
Lists available product categories.

**Output (JSON):**
```json
{
  "categories": [
    {
      "name": "appliances",
      "display_name": "Home Appliances",
      "attributes": 50,
      "required_fields": ["Voltage Rating", "Amperage Rating", "Material"]
    }
  ]
}
```

---

## GET /health
Service health check.

**Output (JSON):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pipeline_ready": true,
  "categories_available": 1
}
```
