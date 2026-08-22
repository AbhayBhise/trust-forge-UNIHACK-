"""Test full pipeline output on actual dataset rows"""
import sys
import csv
sys.path.insert(0, 'files')
from desc_extraction_provider import DescriptionExtractionProvider

p = DescriptionExtractionProvider()

with open('Unihack_ Sample Dataset - Input.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Test first 10 rows with full bundle output
for i, row in enumerate(rows[:10]):
    result = p.fetch_from_row(row)
    facts = result.get('facts', {})
    mpn = row.get('Mfg_Part_Num', '?')
    brand = result.get('_brand_name', '?')
    manuf = result.get('_manufacturer_name', '?')
    cat = result.get('_category', '?')
    series = result.get('_series', '')
    
    print(f"\n--- Row {i+1}: {mpn} ---")
    print(f"  Brand: {brand} | Manuf: {manuf}")
    print(f"  Category: {cat}")
    if series:
        print(f"  Series: {series}")
    print(f"  Facts ({len(facts)}):")
    for k, v in facts.items():
        print(f"    {k}: {v[0]}")
