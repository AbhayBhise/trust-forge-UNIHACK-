"""Test description extraction on actual dataset rows"""
import sys
import csv
sys.path.insert(0, 'files')
from desc_extraction_provider import DescriptionExtractionProvider

p = DescriptionExtractionProvider()

with open('Unihack_ Sample Dataset - Input.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Dataset: {len(rows)} rows")
print(f"Columns: {list(rows[0].keys())[:10]}...")
print()

# Test first 20 rows
for i, row in enumerate(rows[:20]):
    result = p.fetch_from_row(row)
    facts = result.get('facts', {})
    mpn = row.get('Mfg_Part_Num', '?')
    desc = row.get('Part_Desc', '')[:60]
    cat = result.get('_category', '?')
    print(f"{i+1:3d}. {mpn:20s} | {len(facts):2d} attrs | {cat:25s} | {desc}...")

# Summary stats
print("\n--- Summary (first 50 rows) ---")
attr_counts = []
for row in rows[:50]:
    result = p.fetch_from_row(row)
    facts = result.get('facts', {})
    attr_counts.append(len(facts))

print(f"Min attrs: {min(attr_counts)}")
print(f"Max attrs: {max(attr_counts)}")
print(f"Avg attrs: {sum(attr_counts)/len(attr_counts):.1f}")
print(f"Rows with 5+ attrs: {sum(1 for c in attr_counts if c >= 5)}/{len(attr_counts)}")
print(f"Rows with 3+ attrs: {sum(1 for c in attr_counts if c >= 3)}/{len(attr_counts)}")
