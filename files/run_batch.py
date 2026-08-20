"""
Batch processor — handles large datasets with parallel processing.
Supports 1 to 100,000+ rows with configurable worker count.
"""
import csv
import json
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pipeline import build_product, deduplicate
from eval import CompositeProvider, load_input_rows

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_WORKERS = 20


def process_row_safe(row, provider):
    try:
        return build_product(row, provider)
    except Exception as e:
        from models import Product, Identity
        p = Product()
        p.mfg_part_num = row.get("Mfg_Part_Num", "UNKNOWN")
        p.manufacturer_name = row.get("Part_Manuf", "UNKNOWN")
        p.brand_name = row.get("E1_Brand", "UNKNOWN")
        p.identity = Identity(status="needs_review", matched_on="error")
        p.quality_score = {"completeness": 0.0, "validation_pass_rate": 0.0, "mean_confidence": 0.0, "evidence_coverage": 0.0}
        p.attributes = []
        p.descriptions = {}
        return p


def run_batch(max_rows=None, workers=MAX_WORKERS):
    input_rows = load_input_rows()
    unique_rows, dup_map = deduplicate(input_rows)
    
    if max_rows:
        unique_rows = unique_rows[:max_rows]
    
    total = len(unique_rows)
    print(f"Processing {total} unique products with {workers} parallel workers...")
    
    provider = CompositeProvider()
    start_time = time.time()
    
    products = [None] * total
    verified = 0
    needs_review = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, row in enumerate(unique_rows):
            future = executor.submit(process_row_safe, row, provider)
            futures[future] = i
        
        for i, future in enumerate(as_completed(futures)):
            idx = futures[future]
            try:
                product = future.result()
                products[idx] = product
                
                if product.identity.status == "verified":
                    verified += 1
                else:
                    needs_review += 1
            except Exception:
                failed += 1
                row = unique_rows[idx]
                p = Product()
                p.mfg_part_num = row.get("Mfg_Part_Num", "UNKNOWN")
                p.identity = Identity(status="needs_review", matched_on="error")
                p.quality_score = {"completeness": 0.0, "validation_pass_rate": 0.0, "mean_confidence": 0.0, "evidence_coverage": 0.0}
                p.attributes = []
                p.descriptions = {}
                products[idx] = p
            
            if (i + 1) % max(1, total // 20) == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (total - i - 1) / rate if rate > 0 else 0
                print(f"  [{i+1}/{total}] {verified} verified, {needs_review} needs_review, "
                      f"{rate:.1f} rows/sec, ETA: {eta:.0f}s")
    
    # Filter out None products (shouldn't happen but safety)
    products = [p for p in products if p is not None]
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Compute stats
    total_confidence = sum(p.quality_score.get("mean_confidence", 0.0) for p in products)
    total_val_pass = sum(p.quality_score.get("validation_pass_rate", 0.0) for p in products)
    missing_docs = sum(1 for p in products if p.quality_score.get("evidence_coverage", 0.0) == 0.0)
    
    stats = {
        "total_products": len(products),
        "verified": verified,
        "needs_review": needs_review,
        "failed": failed,
        "missing_docs": missing_docs,
        "duplicates": len(input_rows) - len(unique_rows),
        "avg_confidence": total_confidence / len(products) if products else 0,
        "avg_validation_pass_rate": total_val_pass / len(products) if products else 0,
        "avg_processing_time_ms": (elapsed / len(products) * 1000) if products else 0,
        "total_time_sec": elapsed,
        "throughput": len(products) / elapsed if elapsed > 0 else 0,
    }
    
    print("\n" + "=" * 50)
    print("  BATCH PROCESSING COMPLETE")
    print("=" * 50)
    print(f"  Total Products     : {stats['total_products']}")
    print(f"  Duplicates Dropped : {stats['duplicates']}")
    print(f"  Verified           : {stats['verified']}")
    print(f"  Needs Review       : {stats['needs_review']}")
    print(f"  Failed             : {stats['failed']}")
    print(f"  Missing Docs       : {stats['missing_docs']}")
    print(f"  Avg Confidence     : {stats['avg_confidence']*100:.1f}%")
    print(f"  Validation Pass    : {stats['avg_validation_pass_rate']*100:.1f}%")
    print(f"  Total Time         : {stats['total_time_sec']:.1f}s")
    print(f"  Throughput         : {stats['throughput']:.1f} rows/sec")
    print(f"  Avg Time/Product   : {stats['avg_processing_time_ms']:.1f}ms")
    print("=" * 50)
    
    # Save demo output JSON
    demo_data = [p.to_dict() for p in products]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output.json")
    with open(out_path, "w") as f:
        json.dump(demo_data, f, indent=2)
    print(f"\nSaved {len(demo_data)} products to demo_output.json")
    
    return products, stats


if __name__ == "__main__":
    max_rows = int(sys.argv[1]) if len(sys.argv) > 1 else None
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_WORKERS
    run_batch(max_rows, workers)
