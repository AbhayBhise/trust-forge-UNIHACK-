"""
Tests for column_detector module - smart CSV column detection.
"""
import unittest
from column_detector import detect_columns, map_row, detect_and_report, normalize_column_name


class TestColumnDetector(unittest.TestCase):
    
    def test_standard_columns(self):
        """Test detection with standard Unilog column names."""
        headers = ["Mfg_Part_Num", "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf"]
        result = detect_columns(headers)
        
        self.assertEqual(result["Mfg_Part_Num"], "Mfg_Part_Num")
        self.assertEqual(result["Part_Desc"], "Part_Desc")
        self.assertEqual(result["E1_Brand"], "E1_Brand")
        self.assertEqual(result["Unilog_Brand"], "Unilog_Brand")
        self.assertEqual(result["DIB_Brand"], "DIB_Brand")
        self.assertEqual(result["Part_Manuf"], "Part_Manuf")
    
    def test_alternative_names(self):
        """Test detection with alternative column names."""
        headers = ["MPN", "Description", "Brand", "Manufacturer", "SKU"]
        result = detect_columns(headers)
        
        self.assertEqual(result["Mfg_Part_Num"], "MPN")
        self.assertEqual(result["Part_Desc"], "Description")
        self.assertEqual(result["E1_Brand"], "Brand")
        self.assertEqual(result["Part_Manuf"], "Manufacturer")
    
    def test_case_insensitive(self):
        """Test detection is case insensitive."""
        headers = ["mpn", "DESCRIPTION", "brand", "manufacturer"]
        result = detect_columns(headers)
        
        self.assertEqual(result["Mfg_Part_Num"], "mpn")
        self.assertEqual(result["Part_Desc"], "DESCRIPTION")
        self.assertEqual(result["E1_Brand"], "brand")
        self.assertEqual(result["Part_Manuf"], "manufacturer")
    
    def test_underscore_variations(self):
        """Test detection with underscore variations."""
        headers = ["part_number", "product_description", "brand_name", "vendor_name"]
        result = detect_columns(headers)
        
        self.assertEqual(result["Mfg_Part_Num"], "part_number")
        self.assertEqual(result["Part_Desc"], "product_description")
        self.assertEqual(result["E1_Brand"], "brand_name")
        self.assertEqual(result["Part_Manuf"], "vendor_name")
    
    def test_missing_columns(self):
        """Test detection with missing columns."""
        headers = ["MPN", "Description"]
        result = detect_columns(headers)
        
        self.assertEqual(result["Mfg_Part_Num"], "MPN")
        self.assertEqual(result["Part_Desc"], "Description")
        self.assertIsNone(result["E1_Brand"])
        self.assertIsNone(result["Part_Manuf"])
    
    def test_empty_headers(self):
        """Test detection with empty headers."""
        headers = []
        result = detect_columns(headers)
        
        for field in result.values():
            self.assertIsNone(field)
    
    def test_map_row(self):
        """Test row mapping with column map."""
        row = {"MPN": "PDSH4816AF", "Description": "Dishwasher", "Brand": "Frigidaire", "Manufacturer": "Rheem"}
        column_map = {"Mfg_Part_Num": "MPN", "Part_Desc": "Description", "E1_Brand": "Brand", "Part_Manuf": "Manufacturer"}
        
        result = map_row(row, column_map)
        
        self.assertEqual(result["Mfg_Part_Num"], "PDSH4816AF")
        self.assertEqual(result["Part_Desc"], "Dishwasher")
        self.assertEqual(result["E1_Brand"], "Frigidaire")
        self.assertEqual(result["Part_Manuf"], "Rheem")
    
    def test_map_row_with_placeholders(self):
        """Test row mapping filters placeholder values."""
        row = {"MPN": "TEST", "Brand": "-- Unbranded --", "UnilogBrand": "-- No Unilog Brand --"}
        column_map = {"Mfg_Part_Num": "MPN", "E1_Brand": "Brand", "Unilog_Brand": "UnilogBrand"}
        
        result = map_row(row, column_map)
        
        self.assertEqual(result["Mfg_Part_Num"], "TEST")
        self.assertEqual(result["E1_Brand"], "")  # Placeholder filtered
        self.assertEqual(result["Unilog_Brand"], "")  # Placeholder filtered
    
    def test_map_row_missing_columns(self):
        """Test row mapping with missing columns."""
        row = {"MPN": "TEST"}
        column_map = {"Mfg_Part_Num": "MPN", "Part_Desc": "Description", "E1_Brand": "Brand"}
        
        result = map_row(row, column_map)
        
        self.assertEqual(result["Mfg_Part_Num"], "TEST")
        self.assertEqual(result["Part_Desc"], "")  # Missing column
        self.assertEqual(result["E1_Brand"], "")  # Missing column
    
    def test_detect_and_report_success(self):
        """Test detect_and_report with valid columns."""
        headers = ["MPN", "Description", "Brand", "Manufacturer"]
        column_map, warnings = detect_and_report(headers)
        
        self.assertEqual(column_map["Mfg_Part_Num"], "MPN")
        self.assertTrue(any("Detected columns" in w for w in warnings))
    
    def test_detect_and_report_critical_missing(self):
        """Test detect_and_report with critical column missing."""
        headers = ["Description", "Brand"]
        column_map, warnings = detect_and_report(headers)
        
        self.assertIsNone(column_map["Mfg_Part_Num"])
        self.assertTrue(any("CRITICAL" in w for w in warnings))
    
    def test_normalize_column_name(self):
        """Test column name normalization."""
        self.assertEqual(normalize_column_name("Mfg_Part_Num"), "mfgpartnum")
        self.assertEqual(normalize_column_name("Mfg Part Num"), "mfgpartnum")
        self.assertEqual(normalize_column_name("MPN"), "mpn")
        self.assertEqual(normalize_column_name("  MPN  "), "mpn")


if __name__ == "__main__":
    unittest.main()
