import unittest
from models import Product, Attribute, Identity, ValidationEntry
from pipeline import _validate_attribute, _score_confidence

class TestValidationRobustness(unittest.TestCase):
    def setUp(self):
        self.product = Product(mfg_part_num="123", part_desc="Dishwasher")
        self.product.identity = Identity(status="verified", matched_on="mpn")
        self.product.classpath = "Appliances"
        self.product.manufacturer_name = "TestMfg"
        import config_appliances
        self.product._cfg = config_appliances

    def test_wrong_units(self):
        attr = Attribute(attribute="Voltage Rating", value="120", uom="Hz", required=True)
        # Assuming we expect 'V'
        _validate_attribute(attr, self.product, "number", "V")
        _score_confidence(attr, self.product)
        
        self.assertEqual(attr.checks["unit_normalized"], False)
        # Should contain a failing rule for unit
        fails = [v for v in attr.validation_report if v.result == "FAIL"]
        self.assertTrue(any("unit normalized" in v.rule for v in fails))
        # Confidence should be penalized
        self.assertTrue(attr.confidence < 1.0)
        
    def test_missing_manufacturer_evidence(self):
        attr = Attribute(attribute="Voltage Rating", value="120", uom="V", required=True)
        # No evidence attached
        _validate_attribute(attr, self.product, "number", "V")
        _score_confidence(attr, self.product)
        
        self.assertEqual(attr.checks["manufacturer_match"], False)
        self.assertTrue(attr.confidence < 1.0)

    def test_missing_required_field(self):
        attr = Attribute(attribute="Voltage Rating", value=None, uom="V", required=True)
        _validate_attribute(attr, self.product, "number", "V")
        _score_confidence(attr, self.product)
        
        self.assertEqual(attr.status, "unknown")
        # Ensure it has a failure for the missing required field
        fails = [v for v in attr.validation_report if v.result == "FAIL"]
        self.assertTrue(any("present" in v.rule for v in fails))
        
if __name__ == "__main__":
    unittest.main()
