import unittest
import re
from models import Product, Attribute, Identity
from pipeline import _render_descriptions
import config_appliances as cfg

class TestTemplateRobustness(unittest.TestCase):
    def setUp(self):
        self.product = Product(mfg_part_num="123", part_desc="Test Dishwasher")
        self.product.manufacturer_name = "TestMfg"
        self.product.brand_name = "TestBrand"
        self.product.identity = Identity(status="verified", matched_on="mpn")
        self.product._cfg = cfg
        
        # Populate all attributes
        for label, dtype, uom, req in cfg.ATTRIBUTES:
            attr = Attribute(attribute=label)
            if label == "Series": attr.value = "Test Series"
            elif label == "Number of Wash Cycles": attr.value = "5"
            elif label == "Voltage Rating": attr.value = "120"
            elif label == "Amperage Rating": attr.value = "15"
            elif label == "Mounting Type": attr.value = "Leg"
            elif label == "Material": attr.value = "Stainless Steel"
            elif label == "Size": attr.value = "24 in W x 24 in D"
            elif label == "Depth With Door Open": attr.value = "50"
            elif label == "Sound Level": attr.value = "45"
            self.product.attributes.append(attr)

    def _assert_clean_text(self, text):
        self.assertNotIn(" ,", text)
        self.assertNotIn(",,", text)
        self.assertNotIn(" -Wash", text) # no dangling hyphens
        self.assertNotIn(", -Wash", text)
        self.assertFalse(text.endswith(","))

    def test_full_attributes(self):
        _render_descriptions(self.product, {})
        for k, v in self.product.descriptions.items():
            self._assert_clean_text(v)
            self.assertTrue(len(v) > 0)

    def test_missing_cycles(self):
        attr = self.product.get_attr("Number of Wash Cycles")
        attr.value = None
        _render_descriptions(self.product, {})
        short_desc = self.product.descriptions["SHORT_DESC"]
        self._assert_clean_text(short_desc)
        self.assertNotIn("Wash Cycle", short_desc)

    def test_missing_voltage_and_amps(self):
        self.product.get_attr("Voltage Rating").value = None
        self.product.get_attr("Amperage Rating").value = None
        _render_descriptions(self.product, {})
        long_desc = self.product.descriptions["LONG_DESC1"]
        self._assert_clean_text(long_desc)
        self.assertNotIn("V,", long_desc)
        self.assertNotIn("A,", long_desc)
        
    def test_all_missing(self):
        for attr in self.product.attributes:
            attr.value = None
        _render_descriptions(self.product, {})
        for k, v in self.product.descriptions.items():
            self._assert_clean_text(v)
            
if __name__ == "__main__":
    unittest.main()
