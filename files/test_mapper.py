import unittest
from models import Product, Attribute, Evidence
from export_mapper import map_to_delivery_format

class TestExportMapper(unittest.TestCase):
    def test_mapper(self):
        # 1. Setup mock product
        p = Product(mfg_part_num="123", part_desc="Desc")
        p.manufacturer_name = "Rheem"
        p.brand_name = "Frigidaire"
        p.classpath = "Appliances"
        
        p.descriptions = {
            "SHORT_DESC": "Short",
            "LONG_DESC1": "Long"
        }
        
        a1 = Attribute(attribute="Voltage Rating", value="120", uom="V")
        a1.evidence.append(Evidence("http://example.com", 3))
        a2 = Attribute(attribute="Amperage Rating", value="15", uom="A")
        
        p.attributes = [a1, a2]
        
        # 2. Setup raw headers
        headers = ["MFR URL", "MANUFACTURER_NAME", "BRAND_NAME", "Classpath", "SHORT_DESC", "LONG_DESC1"]
        for i in range(1, 51):
            headers.extend([f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"])
            
        original_row = {"MFR URL": "", "MANUFACTURER_NAME": "Old"}
        
        # 3. Map
        mapped = map_to_delivery_format(p, original_row, headers)
        
        # 4. Verify
        self.assertEqual(mapped["MANUFACTURER_NAME"], "Rheem")
        self.assertEqual(mapped["MFR URL"], "http://example.com")
        self.assertEqual(mapped["SHORT_DESC"], "Short")
        
        # Voltage Rating is index 4 in config_appliances.ATTRIBUTES (Series=1, Model=2, Cycles=3, Voltage=4)
        self.assertEqual(mapped["ATTRIBUTE_LABEL 4"], "Voltage Rating")
        self.assertEqual(mapped["ATTRIBUTE_VALUE 4"], "120")
        self.assertEqual(mapped["ATTRIBUTE_UOM 4"], "V")
        
        # Amperage Rating is index 5
        self.assertEqual(mapped["ATTRIBUTE_LABEL 5"], "Amperage Rating")
        self.assertEqual(mapped["ATTRIBUTE_VALUE 5"], "15")
        
        # Mounting Type is index 6 in config - always written but value is empty since we didn't set it
        self.assertEqual(mapped["ATTRIBUTE_LABEL 6"], "Mounting Type")
        self.assertEqual(mapped["ATTRIBUTE_VALUE 6"], "")

if __name__ == "__main__":
    unittest.main()
