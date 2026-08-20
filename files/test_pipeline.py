import unittest
from pipeline import normalize_mpn, deduplicate, resolve_identity, build_product
from models import Product
from desc_extraction_provider import DescriptionExtractionProvider


class MockProvider:
    """Simple mock provider for testing — returns minimal evidence."""
    def fetch(self, mfg_part_num: str) -> dict:
        return {}
    
    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        desc = row.get("Part_Desc", "")
        brand = row.get("E1_Brand", "")
        manuf = row.get("Part_Manuf", "")
        
        facts = {}
        if "120" in desc or "Voltage" in desc:
            from models import Evidence
            ev = Evidence(source_url="test", source_tier=2, page_or_section="test")
            facts["Voltage Rating"] = ("120", "V", ev)
        
        return {
            "_manufacturer_name": manuf or "Test Manufacturer",
            "_brand_name": brand or "Test Brand",
            "_series": "",
            "_mfr_url": "test",
            "facts": facts,
        }


class TestPipeline(unittest.TestCase):
    def test_normalize_mpn(self):
        self.assertEqual(normalize_mpn("WDTS-7024-RZ"), "WDTS7024RZ")
        self.assertEqual(normalize_mpn(" wdts7024rz "), "WDTS7024RZ")
        
    def test_deduplicate(self):
        rows = [
            {"Mfg_Part_Num": "WDTS-7024RZ"},
            {"Mfg_Part_Num": "WDTS7024RZ"}
        ]
        unique, dup_map = deduplicate(rows)
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0]["Mfg_Part_Num"], "WDTS-7024RZ")
        self.assertEqual(dup_map["WDTS7024RZ"], "WDTS-7024RZ")

    def test_resolve_identity_unverified(self):
        row = {"E1_Brand": "-- Unbranded --"}
        identity = resolve_identity(row, evidence_found=False)
        self.assertEqual(identity.status, "unverified")

    def test_resolve_identity_verified(self):
        row = {"E1_Brand": "-- Unbranded --"}
        identity = resolve_identity(row, evidence_found=True)
        self.assertEqual(identity.status, "verified")

    def test_build_product_with_mock_provider(self):
        provider = MockProvider()
        row = {
            "Mfg_Part_Num": "TEST-123",
            "Part_Desc": "TEST-123 Dishwasher SS 120V",
            "E1_Brand": "-- Unbranded --",
            "Unilog_Brand": "-- No Unilog Brand --",
            "DIB_Brand": "-- No DIB Brand --"
        }
        product = build_product(row, provider)
        self.assertEqual(product.mfg_part_num, "TEST-123")
        self.assertEqual(product.identity.status, "verified")
        self.assertEqual(product.manufacturer_name, "Test Manufacturer")
        
        # Check that descriptions were generated
        self.assertIn("INVOICE_DESC", product.descriptions)


if __name__ == '__main__':
    unittest.main()
