"""Check diverse rows across the dataset"""
import sys
import csv
sys.path.insert(0, 'files')
from desc_extraction_provider import DescriptionExtractionProvider

p = DescriptionExtractionProvider()

with open('Unihack_ Sample Dataset - Input.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Sample from various positions
indices = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 999]
for idx in indices:
    if idx >= len(rows):
        continue
    row = rows[idx]
    result = p.fetch_from_row(row)
    facts = result.get('facts', {})
    mpn = row.get('Mfg_Part_Num', '?')
    desc = row.get('Part_Desc', '')[:70]
    cat = result.get('_category', '?')
    brand = result.get('_brand_name', '?') or '-'
    manuf = result.get('_manufacturer_name', '?') or '-'
    
    print(f"\n[{idx:4d}] {mpn:25s} | {len(facts):2d} attrs | {cat:25s} | Brand: {brand:15s} | Manuf: {manuf:25s}")
    print(f"       Desc: {desc}")
    for k, v in facts.items():
        print(f"         {k}: {v[0]}")
