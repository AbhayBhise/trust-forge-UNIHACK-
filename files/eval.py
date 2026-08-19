"""
Lightweight evaluation and provider composition.

Evidence retrieval chain (in priority order):
1. GroundTruthSeedProvider  — Unilog's verified GT CSV (Tier 5)
2. WebEvidenceProvider      — live manufacturer page scraping (Tier 3)
3. PDFEvidenceProvider      — spec sheet PDFs (Tier 4-5)
4. DescriptionExtractionProvider — Doc-First from Part_Desc (Tier 2)
"""
import csv
import json
from pipeline import build_product, deduplicate
from evidence_provider import HardcodedRealDataProvider, EvidenceProvider
from pdf_evidence_provider import PDFEvidenceProvider
from web_evidence_provider import WebEvidenceProvider
from gt_seed_provider import GroundTruthSeedProvider
from desc_extraction_provider import DescriptionExtractionProvider
from html_spec_extractor import SpecBlockExtractor
import os

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CompositeProvider(EvidenceProvider):
    """
    Aggregates multiple evidence backends into one provider.

    Retrieval chain (in priority order):
    1. GroundTruthSeedProvider      — Unilog's verified GT file (Tier 5, instant)
    2. WebEvidenceProvider          — live manufacturer page scraping (Tier 3)
    3. PDFEvidenceProvider          — spec sheet PDFs (Tier 4-5)
    4. DescriptionExtractionProvider— Doc-First from Part_Desc (Tier 2, universal)

    Every row gets at least Tier-2 evidence from the description field.
    Known GT rows get Tier-5 evidence instantly.
    """
    def __init__(self, enable_web=True):
        self.gt_seed = GroundTruthSeedProvider()
        self.desc_extractor = DescriptionExtractionProvider()
        self.pdf = PDFEvidenceProvider()
        self.web = WebEvidenceProvider() if enable_web else None
        self.html_extractor = SpecBlockExtractor()
        # Keep _row for desc extraction (set per-call via fetch_with_row)
        self._current_row: dict = {}

    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        """Full fetch with row context for description extraction."""
        # 1. GT seed — Tier-5 verified data (instant)
        primary = self.gt_seed.fetch(mfg_part_num)
        if primary:
            return primary

        # 2. Web scraping — real manufacturer page
        if self.web:
            web_result = self.web.fetch(mfg_part_num)
            if web_result:
                # Merge with desc extraction for extra fields
                desc_result = self.desc_extractor.fetch_from_row(row)
                if desc_result:
                    # Web takes priority but desc fills gaps
                    merged = dict(desc_result)
                    merged.update(web_result)
                    # Merge facts (desc fills what web missed)
                    merged_facts = dict(desc_result.get("facts", {}))
                    merged_facts.update(web_result.get("facts", {}))
                    merged["facts"] = merged_facts
                    return merged
                return web_result

        # 3. PDF provider
        pdf_result = self.pdf.fetch(mfg_part_num)
        if pdf_result:
            return pdf_result

        # 4. Description extraction — Tier-2, works for ALL rows
        return self.desc_extractor.fetch_from_row(row)

    def fetch(self, mfg_part_num: str) -> dict:
        """Backwards-compatible fetch — uses cached row if available."""
        if self._current_row:
            return self.fetch_with_row(mfg_part_num, self._current_row)
        # Last resort: GT seed or web only
        primary = self.gt_seed.fetch(mfg_part_num)
        if primary:
            return primary
        if self.web:
            return self.web.fetch(mfg_part_num)
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
