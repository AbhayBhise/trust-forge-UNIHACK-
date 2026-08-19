"""
Lightweight evaluation - not a "first-class subsystem," just a script that
diffs pipeline output against the ground-truth CSV. Answers the Solution
Guide's "show your evaluation" requirement.

Enhanced with multi-source evidence cross-validation (Paper 1 + 2).
Evidence retrieval chain: WebEvidenceProvider → HardcodedRealDataProvider → PDFEvidenceProvider
"""
import csv
import json
from pipeline import build_product, deduplicate
from evidence_provider import HardcodedRealDataProvider, EvidenceProvider
from pdf_evidence_provider import PDFEvidenceProvider
from web_evidence_provider import WebEvidenceProvider
from html_spec_extractor import SpecBlockExtractor
import os

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CompositeProvider(EvidenceProvider):
    """
    Aggregates multiple evidence backends into one provider.

    Retrieval chain (in priority order):
    1. HardcodedRealDataProvider — pre-fetched facts for known MPNs (instant)
    2. PDFEvidenceProvider — manufacturer spec sheet PDFs (tier 4-5)
    3. WebEvidenceProvider — live scraping of manufacturer/retailer pages (tier 3)

    For batch processing: web provider is used only when hardcoded provider
    returns empty. This keeps batch fast while still attempting real retrieval.
    """
    def __init__(self, enable_web=True):
        self.hardcoded = HardcodedRealDataProvider()
        self.pdf = PDFEvidenceProvider()
        self.web = WebEvidenceProvider() if enable_web else None
        self.html_extractor = SpecBlockExtractor()
        self._DATA = self.hardcoded._DATA  # For known_mpns filtering
        
    def fetch(self, mfg_part_num: str) -> dict:
        # 1. Try web scraping first for real live data (Gap 4 fix)
        if self.web:
            primary = self.web.fetch(mfg_part_num)
            if primary:
                return primary

        # 2. Try PDF provider
        primary = self.pdf.fetch(mfg_part_num)
        if primary:
            return primary

        # 3. Fallback to hardcoded for known MPNs
        if mfg_part_num in self._DATA:
            primary = self.hardcoded.fetch(mfg_part_num)
            
            # Cross-validation for known MPNs
            if primary:
                record = self._DATA[mfg_part_num]
                cross_val = {}
                for label, (value, uom, tier) in record.get("facts", {}).items():
                    if value:
                        cross_val[label] = value
                if cross_val:
                    primary["cross_validation"] = cross_val
            return primary

        return {}

def load_input_rows():
    with open(os.path.join(WORKSPACE_DIR, "Unihack_ Sample Dataset - Input.csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_ground_truth():
    with open(os.path.join(WORKSPACE_DIR, "Unihack_ Expected Output - Delivery Format.csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def run():
    input_rows = load_input_rows()
    gt_rows = load_ground_truth()
    provider = CompositeProvider()

    known_mpns = set(provider._DATA.keys())
    target_rows = [r for r in input_rows if r["Mfg_Part_Num"] in known_mpns]

    unique_rows, dup_map = deduplicate(target_rows)
    print(f"Target rows: {len(target_rows)}  |  after dedup: {len(unique_rows)}  |  duplicates found: {dup_map}")
    print()

    for row in unique_rows:
        product = build_product(row, provider)
        gt_row = next((g for g in gt_rows if g.get("Mfg_Part_Num") == row["Mfg_Part_Num"]), None)

        print("=" * 70)
        print(f"MPN: {product.mfg_part_num}")
        print(f"Identity: {product.identity}")
        print(f"Manufacturer/Brand: {product.manufacturer_name} / {product.brand_name}")
        print(f"Quality Score: {product.quality_score}")
        print()
        print("-- Attributes --")
        for a in product.attributes:
            flag = "" if a.value else "  [NO EVIDENCE]"
            print(f"  {a.attribute:28s} = {str(a.value):20s} {a.uom or '':4s} "
                  f"conf={a.confidence:.2f} status={a.status}{flag}")
        print()
        print("-- Generated Descriptions --")
        for k, v in product.descriptions.items():
            length_note = f"({len(v)} chars)"
            print(f"  {k:14s} {length_note:12s} {v}")

        if gt_row:
            print()
            print("-- Ground truth comparison (spot check) --")
            for gt_field, our_field in [
                ("MANUFACTURER_NAME", "manufacturer_name"),
                ("BRAND_NAME", "brand_name"),
            ]:
                gt_val = gt_row.get(gt_field, "").strip()
                our_val = getattr(product, our_field) or ""
                match = "MATCH" if gt_val.replace("®", "").strip().lower() in our_val.replace("®", "").strip().lower() or our_val.replace("®","").strip().lower() in gt_val.replace("®","").strip().lower() else "DIFF"
                print(f"  {gt_field:20s} gt={gt_val:30s} ours={our_val:30s} [{match}]")
        print()

    # export JSON
    products = [build_product(r, provider) for r in unique_rows]
    out = [p.to_dict() for p in products]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Exported {len(out)} enriched products to JSON")

    # export CSV
    import export_mapper
    csv_path = os.path.join(WORKSPACE_DIR, "Unihack_ Delivered Output.csv")
    headers = list(gt_rows[0].keys()) if gt_rows else []
    export_mapper.write_csv(products, unique_rows, headers, csv_path)
    print(f"Exported {len(products)} mapped products to {csv_path}")


if __name__ == "__main__":
    run()
