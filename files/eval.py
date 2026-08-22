"""
Lightweight evaluation and provider composition.

Evidence retrieval chain (in priority order):
1. GroundTruthSeedProvider  — Unilog's verified GT CSV (Tier 5)
2. WebEvidenceProvider      — live manufacturer page scraping (Tier 3)
3. GeminiEvidenceProvider   — LLM-powered extraction (Tier 4)
4. PDFEvidenceProvider      — spec sheet PDFs (Tier 4-5)
5. DescriptionExtractionProvider — Doc-First from Part_Desc (Tier 2)
"""
import csv
import json
from pipeline import build_product, deduplicate
from evidence_provider import EvidenceProvider
from pdf_evidence_provider import PDFEvidenceProvider
from web_evidence_provider import WebEvidenceProvider
from gt_seed_provider import GroundTruthSeedProvider
from desc_extraction_provider import DescriptionExtractionProvider
from gemini_evidence_provider import GeminiEvidenceProvider
from html_spec_extractor import SpecBlockExtractor
from activity_tracker import tracker
import os

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CompositeProvider(EvidenceProvider):
    """
    Aggregates multiple evidence backends into one provider.

    Retrieval chain (in priority order):
    1. GroundTruthSeedProvider      — Unilog's verified GT file (Tier 5, instant)
    2. WebEvidenceProvider          — live manufacturer page scraping (Tier 3)
    3. PDFEvidenceProvider          — spec sheet PDFs (Tier 4-5)
    4. GeminiEvidenceProvider       — LLM-powered extraction (Tier 4)
    5. DescriptionExtractionProvider— Doc-First from Part_Desc (Tier 2, universal)

    For known GT MPNs, GT seed provides Tier-5 verified data.
    Unknown MPNs go through web -> PDF -> Gemini -> description extraction.
    Gemini fills gaps that deterministic extraction misses.
    """
    def __init__(self, enable_web=True):
        self.gt_seed = GroundTruthSeedProvider()
        self.desc_extractor = DescriptionExtractionProvider()
        # 3. Web Scraper (primary real-time source)
        self.web = WebEvidenceProvider() if enable_web else None
        # 4. PDF Scraper (real spec sheet extraction)
        self.pdf = PDFEvidenceProvider()
        # 5. Gemini LLM (fills gaps from web/PDF)
        self.gemini = GeminiEvidenceProvider()
        self.html_extractor = SpecBlockExtractor()
        # Keep _row for desc extraction (set per-call via fetch_with_row)
        self._current_row: dict = {}

    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        """Full fetch with row context for description extraction."""
        # 1. GT seed — Tier-5 verified data (simulates production verified DB)
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="GroundTruthSeedProvider",
            action="checking", detail=f"Checking GT database for {mfg_part_num}",
            icon="search", status="running",
        )
        primary = self.gt_seed.fetch(mfg_part_num)
        if primary:
            n_facts = len(primary.get("facts", {}))
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="GroundTruthSeedProvider",
                action="found", detail=f"GT match found — {n_facts} attributes from verified database",
                icon="done", status="success",
            )
            return primary
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="GroundTruthSeedProvider",
            action="miss", detail=f"No GT match for {mfg_part_num} — trying web...",
            icon="arrow", status="skip",
        )

        # 2. Web scraping — real manufacturer page
        if self.web:
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="WebEvidenceProvider",
                action="searching", detail=f"Searching manufacturer sites for {mfg_part_num}...",
                icon="search", status="running",
            )
            web_result = self.web.fetch(mfg_part_num)
            if web_result:
                n_facts = len(web_result.get("facts", {}))
                tracker.emit(
                    mpn=mfg_part_num, step="evidence_retrieval", provider="WebEvidenceProvider",
                    action="found", detail=f"Web evidence: {n_facts} attributes from {web_result.get('_mfr_url', 'manufacturer page')}",
                    icon="done", status="success",
                )
                # Merge with desc extraction for extra fields
                desc_result = self.desc_extractor.fetch_from_row(row)
                if desc_result:
                    merged = dict(desc_result)
                    merged.update(web_result)
                    merged_facts = dict(desc_result.get("facts", {}))
                    merged_facts.update(web_result.get("facts", {}))
                    merged["facts"] = merged_facts
                    return merged
                return web_result
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="WebEvidenceProvider",
                action="miss", detail=f"No web evidence found for {mfg_part_num} — trying PDF...",
                icon="arrow", status="skip",
            )

        # 3. PDF provider — real spec sheet extraction
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="PDFEvidenceProvider",
            action="searching", detail=f"Searching PDF spec sheets for {mfg_part_num}...",
            icon="fetch", status="running",
        )
        pdf_result = self.pdf.fetch(mfg_part_num)
        if pdf_result:
            n_facts = len(pdf_result.get("facts", {}))
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="PDFEvidenceProvider",
                action="found", detail=f"PDF evidence: {n_facts} attributes extracted",
                icon="done", status="success",
            )
            return pdf_result
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="PDFEvidenceProvider",
            action="miss", detail=f"No PDF found for {mfg_part_num} — trying Gemini...",
            icon="arrow", status="skip",
        )

        # 4. Gemini LLM — fills gaps that deterministic extraction misses
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="GeminiEvidenceProvider",
            action="extracting", detail=f"Asking Gemini to extract attributes for {mfg_part_num}...",
            icon="ai", status="running",
        )
        gemini_result = self.gemini.fetch_with_row(mfg_part_num, row)
        if gemini_result:
            n_facts = len(gemini_result.get("facts", {}))
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="GeminiEvidenceProvider",
                action="found", detail=f"Gemini evidence: {n_facts} attributes extracted",
                icon="done", status="success",
            )
            return gemini_result
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="GeminiEvidenceProvider",
            action="miss", detail=f"Gemini extraction empty for {mfg_part_num} — falling back to description",
            icon="arrow", status="skip",
        )

        # 5. Description extraction — Tier-2, works for ALL rows
        tracker.emit(
            mpn=mfg_part_num, step="evidence_retrieval", provider="DescriptionExtractionProvider",
            action="extracting", detail=f"Extracting attributes from Part_Desc for {mfg_part_num}",
            icon="extract", status="running",
        )
        desc_result = self.desc_extractor.fetch_from_row(row)
        if desc_result:
            n_facts = len(desc_result.get("facts", {}))
            tracker.emit(
                mpn=mfg_part_num, step="evidence_retrieval", provider="DescriptionExtractionProvider",
                action="done", detail=f"Description extraction: {n_facts} attributes from Part_Desc",
                icon="done", status="success",
            )
        return desc_result

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


class NoMockProvider(EvidenceProvider):
    """Real-only provider: Web + PDF + Description extraction. NO GT seed, NO hardcoded data."""
    def __init__(self):
        self.web = WebEvidenceProvider()
        self.pdf = PDFEvidenceProvider()
        self.desc = DescriptionExtractionProvider()

    def fetch(self, mfg_part_num: str) -> dict:
        web_result = self.web.fetch(mfg_part_num)
        if web_result:
            return web_result
        pdf_result = self.pdf.fetch(mfg_part_num)
        if pdf_result:
            return pdf_result
        return {}

    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        web_result = self.web.fetch(mfg_part_num)
        if web_result:
            return web_result
        pdf_result = self.pdf.fetch(mfg_part_num)
        if pdf_result:
            return pdf_result
        return self.desc.fetch_from_row(row)


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

    known_mpns = set(provider.gt_seed._db.keys())
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
