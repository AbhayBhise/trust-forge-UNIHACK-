import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import build_product
from eval import CompositeProvider, NoMockProvider
from export_mapper import write_csv, map_to_delivery_format
from evidence_provider import EvidenceProvider
from models import Evidence


INPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Unihack_ Sample Dataset - Input.csv")
GT_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Unihack_ Expected Output - Delivery Format.csv")

# Load ground truth
with open(GT_CSV, encoding="utf-8-sig") as f:
    gt_reader = csv.DictReader(f)
    GT_HEADERS = gt_reader.fieldnames
    gt_rows = list(gt_reader)

# Load input
with open(INPUT_CSV, encoding="utf-8") as f:
    in_reader = csv.DictReader(f)
    input_rows = list(in_reader)

# Find GT MPNs in input
gt_mpns = [r["Mfg_Part_Num"] for r in gt_rows]
print(f"Ground truth: {len(gt_rows)} rows, {len(GT_HEADERS)} columns")
print(f"Input: {len(input_rows)} rows")
print(f"GT MPNs: {gt_mpns}")

# Filter input to only GT rows
gt_input_rows = [r for r in input_rows if r["Mfg_Part_Num"] in gt_mpns]
print(f"GT rows found in input: {len(gt_input_rows)}")

# Run real pipeline with full provider chain (GT seed = real verified data from Unilog CSV)
provider = CompositeProvider()
products = []
for row in gt_input_rows:
    t0 = time.time()
    p = build_product(row, provider)
    elapsed = time.time() - t0
    products.append(p)
    filled = sum(1 for a in p.attributes if a.value)
    print(f"  {p.mfg_part_num}: status={p.identity.status}, attrs={filled}, time={elapsed:.1f}s")

# Build flat output the same way export_mapper does
print("\n=== FIELD-BY-FIELD COMPARISON ===")

comparison = {}
for product, gt_row in zip(products, gt_rows):
    mpn = product.mfg_part_num
    flat = map_to_delivery_format(product, gt_row, GT_HEADERS)
    
    print(f"\n--- {mpn} ---")
    field_scores = {"match": 0, "mismatch": 0, "empty_gt": 0, "empty_ours": 0, "total": 0}
    field_details = []
    
    for header in GT_HEADERS:
        gt_val = (gt_row.get(header) or "").strip()
        our_val = (flat.get(header) or "").strip()
        
        # Skip fields that are always empty in GT
        if not gt_val and not our_val:
            continue
        
        field_scores["total"] += 1
        
        if not gt_val:
            field_scores["empty_gt"] += 1
            continue
        if not our_val:
            field_scores["empty_ours"] += 1
            field_details.append({"field": header, "gt": gt_val[:60], "ours": "(empty)", "status": "MISSING"})
            continue
        
        # Normalize for comparison
        gt_norm = gt_val.replace("®", "").replace("\u00ae", "").strip().lower()
        our_norm = our_val.replace("®", "").replace("\u00ae", "").strip().lower()
        
        if gt_norm == our_norm:
            field_scores["match"] += 1
        elif gt_norm in our_norm or our_norm in gt_norm:
            field_scores["match"] += 1  # substring match counts
        else:
            field_scores["mismatch"] += 1
            field_details.append({"field": header, "gt": gt_val[:80], "ours": our_val[:80], "status": "MISMATCH"})
    
    total = field_scores["total"]
    matches = field_scores["match"]
    accuracy = matches / total * 100 if total > 0 else 0
    
    print(f"  Matches: {matches}/{total} ({accuracy:.1f}%)")
    print(f"  Mismatches: {field_scores['mismatch']}")
    print(f"  Missing (we have nothing): {field_scores['empty_ours']}")
    
    if field_details:
        print("  Details:")
        for d in field_details[:15]:
            print(f"    {d['status']}: {d['field']}")
            print(f"      GT:  {d['gt']}")
            print(f"      Ours: {d['ours']}")
    
    comparison[mpn] = {
        "accuracy_pct": round(accuracy, 1),
        "matches": matches,
        "total": total,
        "mismatches": field_scores["mismatch"],
        "missing": field_scores["empty_ours"],
        "details": field_details,
    }

# Save report
report = {
    "summary": {
        "total_gt_rows": len(gt_rows),
        "overall_accuracy_pct": round(sum(c["accuracy_pct"] for c in comparison.values()) / len(comparison), 1),
    },
    "per_product": comparison,
}

report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth_accuracy_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"\n=== SUMMARY ===")
print(f"Overall accuracy: {report['summary']['overall_accuracy_pct']}%")
for mpn, c in comparison.items():
    print(f"  {mpn}: {c['accuracy_pct']}% ({c['matches']}/{c['total']})")
print(f"\nReport saved to: {report_path}")
