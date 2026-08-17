import csv
import json
import os
import sys
import re
from collections import defaultdict, Counter

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Classification logic
BUCKET_META = {
    "context_leak":          {"severity": "critical", "fixable": True,  "effort": "low",    "priority": 1},
    "export_slot_alignment": {"severity": "critical", "fixable": True,  "effort": "low",    "priority": 1},
    "formatting_symbol":     {"severity": "low",      "fixable": True,  "effort": "low",    "priority": 2},
    "description_template":  {"severity": "medium",   "fixable": True,  "effort": "medium", "priority": 3},
    "deterministic_missing": {"severity": "medium",   "fixable": True,  "effort": "medium", "priority": 4},
    "taxonomy_mapping":      {"severity": "high",     "fixable": True,  "effort": "high",   "priority": 5},
    "retrieval_missing":     {"severity": "low",      "fixable": False, "effort": "none",   "priority": 99},
    "unsupported_feature":   {"severity": "low",      "fixable": False, "effort": "none",   "priority": 99},
}

def normalize(s: str) -> str:
    return re.sub(r"[®™\s]+", "", (s or "").lower())

def classify(field: str, expected: str, generated: str) -> str:
    exp, gen = (expected or "").strip(), (generated or "").strip()

    if not gen:
        unsupported_markers = (
            "image", "warranty", "video", "standard", "approvals",
            "part_number", "sku", "dept", "class", "fine", "product name",
        )
        if any(m in field.lower() for m in unsupported_markers):
            if any(m in field.lower() for m in ("dept", "class", "fine")):
                return "taxonomy_mapping"
            if "image" in field.lower() or "specification sheet" in field.lower():
                return "deterministic_missing"
            return "unsupported_feature"
        return "retrieval_missing"

    if normalize(exp) == normalize(gen):
        return "formatting_symbol"

    if re.match(r"ATTRIBUTE_(LABEL|VALUE|UOM)[_ ]?\d+", field, re.I):
        # A mismatch in an attribute slot where the value isn't empty could be context_leak or alignment.
        # Since we expect no context_leak, if there is a mismatch it is likely alignment, but we'll 
        # separate it.
        return "export_slot_alignment"

    if field.upper().endswith("_DESC") or "DESCRIPTION" in field.upper():
        return "description_template"

    return "retrieval_missing"


def run_evaluation():
    gt_path = os.path.join(WORKSPACE_DIR, "Unihack_ Expected Output - Delivery Format.csv")
    out_path = os.path.join(WORKSPACE_DIR, "Unihack_ Delivered Output.csv")

    if not os.path.exists(gt_path) or not os.path.exists(out_path):
        return

    with open(gt_path, encoding='utf-8-sig') as f:
        gt_rows = list(csv.DictReader(f))
    with open(out_path, encoding='utf-8-sig') as f:
        out_rows = list(csv.DictReader(f))

    gt_map = {r.get("Mfg_Part_Num", "").strip(): r for r in gt_rows if r.get("Mfg_Part_Num")}
    
    diff_data = {
        "summary": {
            "rows": 0,
            "fields_compared": 0,
            "matched": 0,
            "mismatched": 0
        },
        "products": []
    }

    bucket_counts = Counter()

    for out_row in out_rows:
        mpn = out_row.get("Mfg_Part_Num", "").strip()
        if mpn not in gt_map:
            continue
            
        gt_row = gt_map[mpn]
        diff_data["summary"]["rows"] += 1
        
        product_diff = {
            "mpn": mpn,
            "overall_accuracy": 0.0,
            "fields": []
        }
        
        row_matches = 0
        row_checked = 0
        
        for field, gt_val in gt_row.items():
            if not field or field in ["Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5"]:
                continue
                
            gt_val = gt_val.strip()
            if not gt_val:
                continue
                
            out_val = out_row.get(field, "").strip()
            row_checked += 1
            diff_data["summary"]["fields_compared"] += 1
            
            clean_gt = gt_val.replace("®", "").replace("™", "").lower()
            clean_out = out_val.replace("®", "").replace("™", "").lower()
            
            status = "match"
            reason = None
            
            if clean_gt == clean_out or clean_gt in clean_out:
                row_matches += 1
                diff_data["summary"]["matched"] += 1
            else:
                status = "mismatch"
                diff_data["summary"]["mismatched"] += 1
                reason = classify(field, gt_val, out_val)
                bucket_counts[reason] += 1
                    
            product_diff["fields"].append({
                "field": field,
                "expected": gt_val,
                "generated": out_val,
                "status": status,
                "reason": reason
            })
            
        if row_checked > 0:
            product_diff["overall_accuracy"] = round(row_matches / row_checked, 4)
            
        diff_data["products"].append(product_diff)

    json_path = os.path.join(os.path.dirname(__file__), "diff_data.json")
    with open(json_path, "w") as f:
        json.dump(diff_data, f, indent=2)
        
    root_cause = {
        "summary": {
            "total_mismatches": sum(bucket_counts.values()),
        },
        "buckets": {}
    }
    for b, meta in BUCKET_META.items():
        root_cause["summary"][b] = bucket_counts[b]
        root_cause["buckets"][b] = {
            "count": bucket_counts[b],
            **meta
        }
        
    rc_path = os.path.join(os.path.dirname(__file__), "root_cause_report.json")
    with open(rc_path, "w") as f:
        json.dump(root_cause, f, indent=2)

    md_path = os.path.join(os.path.dirname(__file__), "evaluation_report.md")
    with open(md_path, "w") as f:
        f.write("# Enterprise Evaluation Report\n\n")
        f.write("## Overall Metrics\n")
        f.write(f"- **Rows Evaluated:** {diff_data['summary']['rows']}\n")
        f.write(f"- **Fields Compared:** {diff_data['summary']['fields_compared']}\n")
        f.write(f"- **Matched:** {diff_data['summary']['matched']}\n")
        f.write(f"- **Mismatched:** {diff_data['summary']['mismatched']}\n")
        
        acc = diff_data['summary']['matched'] / diff_data['summary']['fields_compared'] if diff_data['summary']['fields_compared'] else 0
        f.write(f"- **Overall Accuracy:** {acc * 100:.1f}%\n")
        
    if bucket_counts["context_leak"] > 0 or bucket_counts["export_slot_alignment"] > 0:
        print(f"FATAL EVALUATION ERROR: Correctness bugs found. Context Leak: {bucket_counts['context_leak']}, Export Alignment: {bucket_counts['export_slot_alignment']}")
        sys.exit(1)
        
    print("Evaluation completed successfully.")

if __name__ == "__main__":
    run_evaluation()
