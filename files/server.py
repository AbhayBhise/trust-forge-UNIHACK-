import csv
import io
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import build_product
from eval import CompositeProvider
from models import Product, Identity
from export_mapper import write_csv

def get_headers():
    gt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Unihack_ Expected Output - Delivery Format.csv")
    with open(gt_path, encoding='utf-8-sig') as f:
        return next(csv.reader(f))

HEADERS = get_headers()

app = FastAPI(title="Unilog Trust Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_SCHEMA = ["Mfg_Part_Num", "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf"]
MAX_ROWS = 25
TIMEOUT_SECONDS = 8.0

def process_row_safe(row: dict, provider: CompositeProvider) -> Product:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(build_product, row, provider)
        try:
            return future.result(timeout=TIMEOUT_SECONDS)
        except TimeoutError:
            p = Product()
            p.mfg_part_num = row.get("Mfg_Part_Num", "UNKNOWN")
            p.manufacturer_name = row.get("Part_Manuf", "UNKNOWN")
            p.brand_name = row.get("E1_Brand", "UNKNOWN")
            p.identity = Identity(status="needs_review", matched_on="timeout")
            p.quality_score = {
                "completeness": 0.0, 
                "validation_pass_rate": 0.0, 
                "mean_confidence": 0.0, 
                "evidence_coverage": 0.0
            }
            p.attributes = []
            p.descriptions = {}
            return p

@app.post("/pipeline/process")
async def process_pipeline(file: UploadFile = File(...)):
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
        
    missing_cols = [col for col in REQUIRED_SCHEMA if col not in reader.fieldnames]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Invalid schema. Missing columns: {missing_cols}")
        
    rows = list(reader)
    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="CSV contains no data rows.")
    if len(rows) > MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"Live demo capped at {MAX_ROWS} rows. You uploaded {len(rows)} rows.")
        
    provider = CompositeProvider()
    results = []
    product_objs = []
    
    for row in rows:
        p = process_row_safe(row, provider)
        product_objs.append(p)
        results.append(p.to_dict())
        
    files_dir = os.path.dirname(__file__)
    timestamp = int(time.time())
    export_filename = f"export_{timestamp}.csv"
    export_path = os.path.join(files_dir, export_filename)
    
    write_csv(product_objs, rows, HEADERS, export_path)
        
    return {
        "products": results,
        "csv_url": f"/files/{export_filename}"
    }

# Mount static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
files_dir = os.path.dirname(__file__)

app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")
app.mount("/files", StaticFiles(directory=files_dir), name="files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
