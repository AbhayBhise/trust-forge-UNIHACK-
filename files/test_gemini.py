"""
Tests for Gemini Evidence Provider — real API calls, no mocks.
Verifies that Gemini can extract product attributes from Part_Desc.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_evidence_provider import GeminiEvidenceProvider


class TestGeminiProvider(unittest.TestCase):
    """Test Gemini evidence provider with real API calls."""

    @classmethod
    def setUpClass(cls):
        cls.gemini = GeminiEvidenceProvider()

    def test_gemini_enabled(self):
        """Gemini should be enabled with valid API key."""
        self.assertTrue(self.gemini._enabled)

    def test_gemini_extracts_pdish4816af(self):
        """Gemini should extract attributes for PDSH4816AF."""
        row = {
            "Mfg_Part_Num": "PDSH4816AF",
            "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("PDSH4816AF", row)

        self.assertIn("facts", result)
        self.assertIn("_brand_name", result)
        self.assertIn("_manufacturer_name", result)

        facts = result["facts"]
        self.assertGreater(len(facts), 0, "Should extract at least 1 attribute")

        # Check key attributes exist
        self.assertIn("Series", facts)
        self.assertIn("Voltage Rating", facts)
        self.assertIn("Material", facts)

        # Verify values
        self.assertEqual(facts["Series"][0], "Professional Series")
        self.assertEqual(facts["Voltage Rating"][0], "120")
        self.assertEqual(facts["Material"][0], "Stainless Steel")

    def test_gemini_extracts_wdts7024rz(self):
        """Gemini should extract attributes for WDTS7024RZ."""
        row = {
            "Mfg_Part_Num": "WDTS7024RZ",
            "Part_Desc": "WDTS7024RZ Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("WDTS7024RZ", row)

        facts = result["facts"]
        self.assertGreater(len(facts), 0, "Should extract at least 1 attribute")

        self.assertIn("Series", facts)
        self.assertIn("Voltage Rating", facts)
        self.assertEqual(facts["Series"][0], "Eco Series")
        self.assertEqual(facts["Voltage Rating"][0], "120")

    def test_gemini_brand_inference(self):
        """Gemini should infer correct brand from MPN."""
        row = {
            "Mfg_Part_Num": "PDSH4816AF",
            "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("PDSH4816AF", row)
        brand = result.get("_brand_name", "").lower()
        self.assertIn("frigidaire", brand, f"Expected Frigidaire brand, got: {brand}")

    def test_gemini_manufacturer_inference(self):
        """Gemini should infer correct manufacturer."""
        row = {
            "Mfg_Part_Num": "WDTS7024RZ",
            "Part_Desc": "WDTS7024RZ Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("WDTS7024RZ", row)
        mfr = result.get("_manufacturer_name", "").lower()
        self.assertIn("whirlpool", mfr, f"Expected Whirlpool manufacturer, got: {mfr}")

    def test_gemini_classpath(self):
        """Gemini should classify product into correct category."""
        row = {
            "Mfg_Part_Num": "PDSH4816AF",
            "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("PDSH4816AF", row)
        classpath = result.get("_classpath", "").lower()
        self.assertIn("dishwasher", classpath, f"Expected dishwasher in classpath, got: {classpath}")

    def test_gemini_returns_evidence_objects(self):
        """Each fact should include an Evidence object with source URL."""
        row = {
            "Mfg_Part_Num": "PDSH4816AF",
            "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
            "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
            "E1_Brand": "-- Unbranded --",
        }
        result = self.gemini.fetch_with_row("PDSH4816AF", row)
        facts = result.get("facts", {})

        for label, fact_tuple in facts.items():
            self.assertEqual(len(fact_tuple), 3, f"Fact '{label}' should be (value, uom, evidence)")
            value, uom, ev = fact_tuple
            self.assertTrue(len(value) > 0, f"Fact '{label}' should have non-empty value")
            self.assertIsNotNone(ev, f"Fact '{label}' should have evidence")
            self.assertTrue(
                ev.source_url.startswith("gemini://"),
                f"Evidence source should be gemini://, got: {ev.source_url}",
            )

    def test_gemini_empty_row_returns_empty(self):
        """Empty row should return empty dict."""
        result = self.gemini.fetch_with_row("", {})
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
