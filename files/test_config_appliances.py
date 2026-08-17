import unittest
import config_appliances as cfg

class TestConfigAppliances(unittest.TestCase):
    def test_attributes_defined(self):
        self.assertTrue(len(cfg.ATTRIBUTES) > 0)
        
    def test_templates_defined(self):
        self.assertIn("INVOICE_DESC", cfg.TEMPLATES)
        self.assertIn("SHORT_DESC", cfg.TEMPLATES)
        
    def test_invoice_desc_spacing_fixed(self):
        template = cfg.TEMPLATES["INVOICE_DESC"]
        self.assertIn("{cycles} {material_abbr}", template)
        
if __name__ == '__main__':
    unittest.main()
