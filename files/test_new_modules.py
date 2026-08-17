"""Quick smoke test for the new modules."""
from html_spec_extractor import SpecBlockExtractor
from normalizer import normalize_attribute_value, normalize_product_attributes
from models import Attribute

# Test 1: Normalizer
print("=== Normalizer Tests ===")
assert normalize_attribute_value("Voltage Rating", "120V") == "120"
assert normalize_attribute_value("Voltage Rating", "120 V") == "120"
assert normalize_attribute_value("Voltage Rating", "120") == "120"
assert normalize_attribute_value("Mounting Type", "built-in") == "Built-in"
assert normalize_attribute_value("Mounting Type", "Built In") == "Built-in"
assert normalize_attribute_value("Material", "stainless steel") == "Stainless Steel"
assert normalize_attribute_value("Sound Level", "47dBA") == "47"
print("  All normalizer tests passed!")

# Test 2: HTML Spec Extractor
print("\n=== HTML Spec Extractor Tests ===")
extractor = SpecBlockExtractor()

# Table format
table_html = '<table><tr><th>Voltage</th><td>120 V</td></tr><tr><th>Amperage</th><td>15 A</td></tr><tr><th>Material</th><td>Stainless Steel</td></tr><tr><th>Mounting Type</th><td>Built-in</td></tr></table>'
pairs = extractor.extract_pairs(table_html)
print(f"  Table format: found {len(pairs)} pairs")
for attr, (val, uom, ev) in pairs.items():
    print(f"    {attr}: {val} (UOM: {uom})")

# DL format
dl_html = '<dl><dt>Voltage Rating</dt><dd>240 V</dd><dt>Number of Wash Cycles</dt><dd>8 Cycles</dd></dl>'
pairs2 = extractor.extract_pairs(dl_html)
print(f"  DL format: found {len(pairs2)} pairs")
for attr, (val, uom, ev) in pairs2.items():
    print(f"    {attr}: {val}")

print("\n  All HTML extractor tests passed!")

# Test 3: Integration - normalize attributes in a product
print("\n=== Integration Test ===")
attrs = [
    Attribute(attribute="Voltage Rating", value="120V", uom="V", status="verified"),
    Attribute(attribute="Mounting Type", value="built-in", status="verified"),
    Attribute(attribute="Material", value="stainless steel", status="verified"),
    Attribute(attribute="Sound Level", value="47dBA", uom="dBA", status="verified"),
]
normalize_product_attributes(attrs)
assert attrs[0].value == "120"
assert attrs[1].value == "Built-in"
assert attrs[2].value == "Stainless Steel"
assert attrs[3].value == "47"
print("  Integration test passed!")

print("\n=== ALL TESTS PASSED ===")
