**Version:** 1.0  
**Date:** 2026-08-14  
**Owner:** AI Pipeline  
**Status:** Draft  
**Reviewed By:** User  
**Last Updated:** 2026-08-14  

# API Contracts

This document defines the REST API endpoints that will be exposed by the FastAPI backend in Phase 5.

## POST /pipeline/process
Initiates the trust engine pipeline for a batch of products.

**Input (multipart/form-data):**
File upload containing a CSV with the exact schema:
- `Mfg_Part_Num`
- `Part_Desc`
- `E1_Brand`
- `Unilog_Brand`
- `DIB_Brand`
- `Part_Manuf`

**Output (JSON):**
List of Serialized `Product` objects (matches `models.py::Product.to_dict()`)

**Errors:**
- `400 Bad Request`: Invalid payload format or missing required fields.

---

## GET /product/{id}
Retrieves the complete internal Product model for a specific MPN.

**Input:** Path parameter `id` (Mfg_Part_Num)
**Output (JSON):** Serialized `Product` object (matches `models.py::Product.to_dict()`)
**Errors:**
- `404 Not Found`: MPN does not exist in the system.

---

## GET /decision-log/{id}
Retrieves only the validation reports and evidence chains for a product.

**Input:** Path parameter `id`
**Output (JSON):** List of Attribute objects filtered to show only `attribute`, `evidence`, `checks`, and `validation_report`.
**Errors:**
- `404 Not Found`: MPN does not exist.

---

## GET /quality-score/{id}
Retrieves the aggregate quality metrics for a product.

**Input:** Path parameter `id`
**Output (JSON):**
```json
{
  "completeness": 1.0,
  "validation_pass_rate": 0.85,
  "mean_confidence": 0.76,
  "evidence_coverage": 0.90
}
```
**Errors:**
- `404 Not Found`: MPN does not exist.
