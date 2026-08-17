import csv
import json
import time
import os
from pipeline import build_product, deduplicate
from eval import CompositeProvider, load_input_rows

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_batch(max_rows=None):
    input_rows = load_input_rows()
    unique_rows, dup_map = deduplicate(input_rows)
    
    if max_rows:
        unique_rows = unique_rows[:max_rows]
    
    print(f"Starting batch process of {len(unique_rows)} unique products...")
    
    provider = CompositeProvider()
    
    start_time = time.time()
    products = []
    
    stats = {
        "total_products": len(unique_rows),
        "verified": 0,
        "needs_review": 0,
        "missing_docs": 0,
        "duplicates": len(input_rows) - len(unique_rows),
        "avg_confidence": 0.0,
        "avg_validation_pass_rate": 0.0
    }
    
    total_confidence = 0
    total_val_pass = 0
    
    for idx, row in enumerate(unique_rows):
        product = build_product(row, provider)
        products.append(product)
        
        status = product.identity.status
        if status == "verified":
            stats["verified"] += 1
        else:
            stats["needs_review"] += 1
            
        if product.quality_score.get("evidence_coverage", 0) == 0.0:
            stats["missing_docs"] += 1
            
        total_confidence += product.quality_score.get("mean_confidence", 0.0)
        total_val_pass += product.quality_score.get("validation_pass_rate", 0.0)
        
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1} products...")
            
    end_time = time.time()
    
    if stats["total_products"] > 0:
        stats["avg_confidence"] = total_confidence / stats["total_products"]
        stats["avg_validation_pass_rate"] = total_val_pass / stats["total_products"]
        
    stats["avg_processing_time_ms"] = ((end_time - start_time) / stats["total_products"]) * 1000
    
    print("\n--- ENTERPRISE BATCH STATISTICS ---")
    print(f"Total Products Processed : {stats['total_products']}")
    print(f"Duplicate Products       : {stats['duplicates']}")
    print(f"Verified & Approved      : {stats['verified']}")
    print(f"Needs Review             : {stats['needs_review']}")
    print(f"Missing Manufacturer Docs: {stats['missing_docs']}")
    print(f"Avg Confidence           : {stats['avg_confidence']*100:.1f}%")
    print(f"Validation Pass Rate     : {stats['avg_validation_pass_rate']*100:.1f}%")
    print(f"Avg Processing Time      : {stats['avg_processing_time_ms']:.2f} ms")
    print("-----------------------------------")
    
    # Save demo output JSON for frontend
    demo_data = [p.to_dict() for p in products]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output.json")
    with open(out_path, "w") as f:
        json.dump(demo_data, f, indent=2)
    print(f"\nSaved {len(demo_data)} products to demo_output.json")
    
    return products, stats

if __name__ == "__main__":
    import sys
    max_rows = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_batch(max_rows)
