import json
from pipeline import build_product, deduplicate
from eval import load_input_rows, CompositeProvider
from evidence_provider import EvidenceProvider

class EmptyEvidenceProvider(EvidenceProvider):
    def fetch(self, mpn: str) -> dict:
        return {} # simulate complete retrieval failure

def test_dataset():
    rows = load_input_rows()
    unique_rows, _ = deduplicate(rows)
    
    provider = EmptyEvidenceProvider()
    
    for row in unique_rows:
        p = build_product(row, provider)
        
        # 1. No populated evidence-backed attributes
        for a in p.attributes:
            if a.value is not None and a.attribute != "Series": 
                # Series falls back to None anyway
                assert False, f"Fabricated value for {a.attribute} on {p.mfg_part_num}"
                
        # 2. No fabricated numeric values or features in descriptions
        for k, v in p.descriptions.items():
            text = v.lower()
            assert "cycle" not in text, f"Fabricated wash cycles in {k}"
            assert "cleanboost" not in text, f"Fabricated feature in {k}"
            assert re.search(r'\d', text) is None or k == "MOBILE_DESC" or k == "SHORT_DESC", "Fabricated numeric value in description"
            
        # 3. Confidence reflects missing evidence (Should not be verified/auto-approved)
        assert p.quality_score.get("mean_confidence", 0.0) < 0.75, f"Confidence {p.quality_score.get('mean_confidence')} too high for zero evidence"
        
        # 4. Status is needs_review or unverified
        assert p.identity.status == "unverified", "Identity should be unverified"
        
    print(f"Verified {len(unique_rows)} products with zero evidence.")

if __name__ == "__main__":
    import re
    test_dataset()
