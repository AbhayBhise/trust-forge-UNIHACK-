import unittest
from models import Product, Attribute, Identity, ValidationEntry, Evidence
from pipeline import build_product
from evidence_provider import EvidenceProvider

class MockFailureProvider(EvidenceProvider):
    def fetch(self, mpn: str) -> dict:
        # Simulate 404 / no evidence
        return {}

class MockExceptionProvider(EvidenceProvider):
    def fetch(self, mpn: str) -> dict:
        raise Exception("Network Error")

class MockGoodProvider(EvidenceProvider):
    def fetch(self, mpn: str) -> dict:
        return {
            "_manufacturer_name": "TestMfg",
            "_brand_name": "TestBrand",
            "facts": {
                "Voltage Rating": ("120", "V", Evidence("url", 5, "p1", "now")),
                "Number of Wash Cycles": ("5", "", Evidence("url", 5, "p1", "now"))
            }
        }

class TestQAAudits(unittest.TestCase):
    def test_schema_validation(self):
        # Step 4: Schema validation (no forbidden nulls)
        provider = MockGoodProvider()
        product = build_product({"Mfg_Part_Num": "123", "Part_Desc": "Dishwasher"}, provider)
        d = product.to_dict()
        self.assertIn("mfg_part_num", d)
        self.assertIsNotNone(d["mfg_part_num"])
        self.assertIn("attributes", d)
        self.assertIn("quality_score", d)
        self.assertIn("descriptions", d)
        # Ensure quality score has required keys
        self.assertIn("completeness", d["quality_score"])

    def test_confidence_and_explainability(self):
        # Step 5 & 6: Confidence and Explainability
        provider = MockGoodProvider()
        product = build_product({"Mfg_Part_Num": "123", "Part_Desc": "Dishwasher"}, provider)
        
        voltage = product.get_attr("Voltage Rating")
        # Since it has high tier evidence (5) and passed validation, confidence must be high
        self.assertTrue(voltage.confidence > 0.7)
        # Value must be present
        self.assertEqual(voltage.value, "120")
        # Explainability: must have evidence and a validation report
        self.assertTrue(len(voltage.evidence) > 0)
        self.assertTrue(len(voltage.validation_report) > 0)
        
    def test_failure_recovery_empty(self):
        # Step 7: Failure recovery (Empty / 404)
        provider = MockFailureProvider()
        product = build_product({"Mfg_Part_Num": "123", "Part_Desc": "Dishwasher"}, provider)
        # Should not crash, quality score should reflect poor completeness
        self.assertEqual(product.identity.status, "unverified")
        self.assertEqual(product.quality_score["evidence_coverage"], 0.0)

    def test_failure_recovery_exception(self):
        # Step 7: Failure recovery (Network exception)
        provider = MockExceptionProvider()
        # The pipeline should catch the exception and degrade gracefully
        product = build_product({"Mfg_Part_Num": "123", "Part_Desc": "Dishwasher"}, provider)
        self.assertEqual(product.identity.status, "unverified")
        self.assertEqual(product.quality_score["evidence_coverage"], 0.0)

if __name__ == "__main__":
    unittest.main()
