import unittest
from models import Evidence, ValidationEntry, HistoryEntry, Identity, Attribute, Product

class TestModels(unittest.TestCase):
    def test_product_initialization(self):
        p = Product(mfg_part_num="123", part_desc="Test Part")
        self.assertEqual(p.mfg_part_num, "123")
        self.assertEqual(p.identity.status, "unverified")

    def test_attribute_to_dict(self):
        attr = Attribute(attribute="Voltage", value="120", uom="V", status="verified", confidence=0.95)
        d = attr.to_dict()
        self.assertEqual(d["attribute"], "Voltage")
        self.assertEqual(d["value"], "120")
        self.assertEqual(d["confidence"], 0.95)

    def test_product_get_attr(self):
        p = Product(mfg_part_num="123", part_desc="Test Part")
        attr = Attribute(attribute="Voltage", value="120")
        p.attributes.append(attr)
        
        found = p.get_attr("Voltage")
        self.assertIsNotNone(found)
        self.assertEqual(found.value, "120")
        
        not_found = p.get_attr("Amperage")
        self.assertIsNone(not_found)

if __name__ == '__main__':
    unittest.main()
