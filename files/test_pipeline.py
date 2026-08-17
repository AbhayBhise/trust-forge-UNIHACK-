import unittest
from pipeline import normalize_mpn, deduplicate, resolve_identity, build_product
from models import Product
from evidence_provider import HardcodedRealDataProvider

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
        provider = HardcodedRealDataProvider()
        row = {
            "Mfg_Part_Num": "PDSH4816AF",
            "Part_Desc": "PDSH4816AF Dishwasher SS",
            "E1_Brand": "-- Unbranded --",
            "Unilog_Brand": "-- No Unilog Brand --",
            "DIB_Brand": "-- No DIB Brand --"
        }
        product = build_product(row, provider)
        self.assertEqual(product.mfg_part_num, "PDSH4816AF")
        self.assertEqual(product.identity.status, "verified")
        self.assertEqual(product.manufacturer_name, "Rheem Manufacturing")
        
        # Check an attribute
        voltage = product.get_attr("Voltage Rating")
        self.assertIsNotNone(voltage)
        self.assertEqual(voltage.value, "120")
        
        # Check that descriptions were generated
        self.assertIn("INVOICE_DESC", product.descriptions)
        
if __name__ == '__main__':
    unittest.main()
