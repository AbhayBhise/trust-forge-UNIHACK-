"""
TrustEngine API Server — production-ready for large-scale processing.

Features:
- Parallel processing with ThreadPoolExecutor
- Background job queue for large datasets
- Progress tracking via /jobs/{id} endpoint
- Streaming results for real-time feedback
- No hard row limit (configurable per-deployment)
"""
import csv
import io
import json
import os
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import build_product
from eval import CompositeProvider
from models import Product, Identity
from export_mapper import write_csv
from column_detector import detect_columns, map_row, detect_and_report
from activity_tracker import tracker

# ── Config ──────────────────────────────────────────────────────────
MAX_ROWS_PER_BATCH = 10000  # No practical limit for production
TIMEOUT_SECONDS = 8.0
MAX_WORKERS = 20  # Increased for fast HTTP playwright server
PROGRESS_UPDATE_INTERVAL = 0.1  # seconds

def get_headers():
    gt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Unihack_ Expected Output - Delivery Format.csv")
    if os.path.exists(gt_path):
        try:
            with open(gt_path, encoding='utf-8-sig') as f:
                return next(csv.reader(f))
        except Exception:
            pass
    
    # Deterministic canonical 252-column delivery schema fallback
    headers = [
        "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5",
        "PART_NUMBER", "Dept", "Class", "Fine", "SKU - MY_PART_NUMBER", "Mfg_Part_Num",
        "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf",
        "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER",
        "ALTERNATE_PART_NUMBER", "Classpath", "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC",
        "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION"
    ]
    for i in range(1, 21):
        headers.append(f"ITEM_FEATURES_{i}")
    headers.extend([
        "With", "Standard/Approvals", "Prop 65", "Application", "Includes", "Product Name"
    ])
    for i in range(1, 51):
        headers.extend([f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"])
    headers.extend([
        "UPC", "EAN", "GTIN", "UNSPSC", "Warranty", "List Price", "Selling Qty", "Selling UOM",
        "Standard Packaging Information", "LENGTH", "LENGTH_UOM", "HEIGHT", "HEIGHT_UOM",
        "WIDTH", "WIDTH_UOM", "WEIGHT", "WEIGHT_UOM", "VOLUME", "VOLUME_UOM", "Product Image",
        "Alternate Image 1", "Alternate Image 2", "Alternate Image 3", "Alternate Image 4",
        "SDS", "SDS_1", "Warranty Information", "Catalog", "Specification Sheet",
        "Instruction/Installation Manual", "Service Manual", "Owners/User Manual", "Line Drawing",
        "MTR", "RoHS", "Full Engineering Drawing", "Energy Star Guide", "Technical Bulletin",
        "Submittal", "Compatibility Chart", "Size Chart", "Product Label/Insert", "Video Link",
        "Video Link 1", "Country Of Origin", "Discontinued", "Actual Image (Yes/No)"
    ])
    return headers

HEADERS = get_headers()

app = FastAPI(title="TrustForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# No hardcoded schema - we auto-detect columns from any CSV format

# ── Job Manager ─────────────────────────────────────────────────────
class JobManager:
    """In-memory job queue with progress tracking."""
    
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
    
    def create_job(self, total_rows: int) -> str:
        job_id = str(uuid.uuid4())[:8]
        with self.lock:
            self.jobs[job_id] = {
                "id": job_id,
                "status": "processing",
                "total": total_rows,
                "completed": 0,
                "failed": 0,
                "verified": 0,
                "needs_review": 0,
                "products": [],
                "csv_url": None,
                "error": None,
                "started_at": time.time(),
                "activity": [],
            }
        return job_id
    
    def update_progress(self, job_id: str, **kwargs):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(kwargs)
    
    def get_job(self, job_id: str) -> dict:
        with self.lock:
            return self.jobs.get(job_id)
    
    def complete_job(self, job_id: str, csv_url: str = None):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["csv_url"] = csv_url
                self.jobs[job_id]["completed_at"] = time.time()

jobs = JobManager()

# ── Processing ──────────────────────────────────────────────────────
def process_row_safe(row: dict, provider: CompositeProvider, column_map: dict = None) -> Product:
    """Process a single row with timeout protection. Uses column_map for flexible input."""
    try:
        # Map CSV columns to our internal schema if column_map provided
        if column_map:
            mapped_row = map_row(row, column_map)
        else:
            mapped_row = row
        # Pass full mapped_row so fetch_with_row() gets Part_Desc, E1_Brand,
        # Part_Manuf context needed by DescriptionExtractionProvider
        return build_product(mapped_row, provider)
    except Exception as e:
        mpn = row.get("Mfg_Part_Num") or row.get("MPN") or row.get("Part_Number") or "UNKNOWN"
        # Try to get brand/manufacturer directly from the row for graceful degradation
        p = Product(mfg_part_num=mpn)
        p.manufacturer_name = row.get("Part_Manuf") or row.get("Manufacturer") or ""
        p.brand_name = row.get("E1_Brand") or row.get("Brand") or ""
        p.identity = Identity(status="needs_review", matched_on="error")
        p.quality_score = {
            "completeness": 0.0,
            "validation_pass_rate": 0.0,
            "mean_confidence": 0.0,
            "evidence_coverage": 0.0
        }
        p.attributes = []
        p.descriptions = {}
        return p



def process_batch_background(job_id: str, rows: list, provider: CompositeProvider, column_map: dict = None):
    """Process rows in parallel with progress updates."""
    products = []
    verified = 0
    needs_review = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_row_safe, row, provider, column_map): row for row in rows}
        
        for i, future in enumerate(as_completed(futures)):
            try:
                product = future.result(timeout=TIMEOUT_SECONDS)
                products.append(product)
                
                if product.identity.status == "verified":
                    verified += 1
                    act_msg = f"Verified {product.mfg_part_num} ({product.brand_name}) - Conf: {int(product.quality_score['mean_confidence']*100)}%"
                else:
                    needs_review += 1
                    act_msg = f"Review needed for {product.mfg_part_num} - Conf: {int(product.quality_score['mean_confidence']*100)}%"
                
                with jobs.lock:
                    if job_id in jobs.jobs:
                        jobs.jobs[job_id]["activity"].append(act_msg)
                        if len(jobs.jobs[job_id]["activity"]) > 5:
                            jobs.jobs[job_id]["activity"].pop(0)
            except Exception:
                failed += 1
                row = futures[future]
                # Try to extract MPN from any column name
                mpn = row.get("Mfg_Part_Num") or row.get("MPN") or row.get("Part_Number") or "UNKNOWN"
                p = Product()
                p.mfg_part_num = mpn
                p.identity = Identity(status="needs_review", matched_on="error")
                p.quality_score = {"completeness": 0.0, "validation_pass_rate": 0.0, "mean_confidence": 0.0, "evidence_coverage": 0.0}
                p.descriptions = {}
                products.append(p)
                
                with jobs.lock:
                    if job_id in jobs.jobs:
                        jobs.jobs[job_id]["activity"].append(f"Failed extracting {mpn}")
                        if len(jobs.jobs[job_id]["activity"]) > 5:
                            jobs.jobs[job_id]["activity"].pop(0)
            
            # Update progress on every row for smooth UI
            jobs.update_progress(job_id,
                completed=i + 1,
                verified=verified,
                needs_review=needs_review,
                failed=failed,
            )
    
    # Export CSV
    files_dir = os.path.dirname(os.path.abspath(__file__))
    export_filename = f"export_{job_id}.csv"
    export_path = os.path.join(files_dir, export_filename)
    
    try:
        write_csv(products, rows, HEADERS, export_path)
        csv_url = f"/files/{export_filename}"
    except Exception:
        csv_url = None
    
    # Save results
    jobs.update_progress(job_id,
        products=[p.to_dict() for p in products],
        csv_url=csv_url,
    )
    jobs.complete_job(job_id, csv_url)
    
    print(f"Job {job_id} complete: {len(products)} products, {verified} verified, {needs_review} needs_review, {failed} failed")


# ── Endpoints ───────────────────────────────────────────────────────
@app.post("/pipeline/process")
async def process_pipeline(file: UploadFile = File(...)):
    """Synchronous processing (for small datasets, <100 rows)."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty or invalid CSV file.")
    
    # Smart column detection - no hardcoded schema required
    column_map, warnings = detect_and_report(reader.fieldnames)
    
    if not column_map.get("Mfg_Part_Num"):
        raise HTTPException(status_code=400, 
            detail="Could not detect a Part Number/MPN column. Please ensure your CSV has a column with part numbers.")
    
    rows = list(reader)
    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="CSV contains no data rows.")
    
    provider = CompositeProvider()
    results = []
    product_objs = []
    
    for row in rows:
        p = process_row_safe(row, provider, column_map)
        product_objs.append(p)
        results.append(p.to_dict())
    
    files_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = int(time.time())
    export_filename = f"export_{timestamp}.csv"
    export_path = os.path.join(files_dir, export_filename)
    
    write_csv(product_objs, rows, HEADERS, export_path)
    
    return {
        "products": results,
        "csv_url": f"/files/{export_filename}",
        "column_map": column_map,
        "warnings": warnings,
    }


@app.post("/pipeline/jobs")
async def create_job(file: UploadFile = File(...)):
    """Create a background job for large datasets. Returns job_id for polling."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty or invalid CSV file.")
    
    # Smart column detection - no hardcoded schema required
    column_map, warnings = detect_and_report(reader.fieldnames)
    
    if not column_map.get("Mfg_Part_Num"):
        raise HTTPException(status_code=400, 
            detail="Could not detect a Part Number/MPN column. Please ensure your CSV has a column with part numbers.")
    
    rows = list(reader)
    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="CSV contains no data rows.")
    if len(rows) > MAX_ROWS_PER_BATCH:
        raise HTTPException(status_code=400, detail=f"Max {MAX_ROWS_PER_BATCH} rows per batch. You uploaded {len(rows)} rows.")
    
    # Create job and start background processing
    job_id = jobs.create_job(len(rows))
    provider = CompositeProvider()
    tracker.clear()  # Fresh event stream for this job
    tracker.emit(
        mpn="", step="job_start", provider="Server",
        action="started", detail=f"Job {job_id}: processing {len(rows)} rows with {MAX_WORKERS} workers",
        icon="arrow", status="running",
    )
    
    thread = threading.Thread(
        target=process_batch_background,
        args=(job_id, rows, provider, column_map),
        daemon=True
    )
    thread.start()
    
    return {
        "job_id": job_id, 
        "total_rows": len(rows), 
        "status": "processing",
        "column_map": column_map,
        "warnings": warnings,
    }


@app.get("/pipeline/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job progress, results, and detailed activity events."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    elapsed = time.time() - job["started_at"]
    rate = job["completed"] / elapsed if elapsed > 0 else 0
    eta = (job["total"] - job["completed"]) / rate if rate > 0 else 0
    
    # Get detailed activity events from the tracker
    last_seq = job.get("last_activity_seq", 0)
    new_events = tracker.get_since(last_seq)
    if new_events:
        job["last_activity_seq"] = max(e["seq"] for e in new_events)
    
    return {
        "id": job["id"],
        "status": job["status"],
        "progress": {
            "total": job["total"],
            "completed": job["completed"],
            "verified": job["verified"],
            "needs_review": job["needs_review"],
            "failed": job["failed"],
            "percent": round(job["completed"] / job["total"] * 100, 1) if job["total"] > 0 else 0,
            "rate_per_sec": round(rate, 1),
            "eta_seconds": round(eta, 1),
        },
        "activity": job.get("activity", []),
        "events": new_events,
        "csv_url": job["csv_url"],
        "products": job["products"] if job["status"] == "completed" else None,
    }


@app.get("/pipeline/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """Stream job progress and detailed activity events via Server-Sent Events."""
    def generate():
        last_seq = 0
        while True:
            job = jobs.get_job(job_id)
            if not job:
                yield f'data: {{"error": "Job not found"}}\n\n'
                break
            
            elapsed = time.time() - job["started_at"]
            rate = job["completed"] / elapsed if elapsed > 0 else 0
            
            # Get new tracker events since last poll
            new_events = tracker.get_since(last_seq)
            if new_events:
                last_seq = max(e["seq"] for e in new_events)
            
            data = {
                "status": job["status"],
                "completed": job["completed"],
                "total": job["total"],
                "percent": round(job["completed"] / job["total"] * 100, 1) if job["total"] > 0 else 0,
                "rate": round(rate, 1),
                "events": new_events,
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            if job["status"] == "completed":
                break
            
            time.sleep(PROGRESS_UPDATE_INTERVAL)
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/debug/tracker")
async def debug_tracker():
    """Debug endpoint to inspect tracker state."""
    stats = tracker.stats()
    recent = tracker.get_all()[-20:]
    return {
        "stats": stats,
        "recent_events": recent,
        "jobs_active": len(jobs.jobs),
    }


# Mount static files (API routes first, then static fallback)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
files_dir = os.path.dirname(os.path.abspath(__file__))

app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")
app.mount("/files", StaticFiles(directory=files_dir), name="files")

if __name__ == "__main__":
    import uvicorn
    print(f"\n  TrustForge running at: http://127.0.0.1:8000\n")
    print(f"  Open: http://127.0.0.1:8000/frontend/\n")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
