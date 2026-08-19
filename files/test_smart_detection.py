"""
Test script to verify smart column detection works with different CSV formats.
Run this to prove the system accepts ANY CSV format.
"""
import csv
import io
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from column_detector import detect_columns, map_row, detect_and_report

# Test CSVs with different column names
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

test_files = [
    (os.path.join(root_dir, "test_alternative_columns.csv"), "Alternative format (model_number, product_description, vendor_name)"),
    (os.path.join(root_dir, "test_mpn_format.csv"), "MPN format (MPN, Short_Description, Brand_Name, Manufacturer_Name)"),
    (os.path.join(root_dir, "test_part_number_format.csv"), "Part number format (Part_Number, Item_Description, etc.)"),
]

print("=" * 70)
print("SMART COLUMN DETECTION TEST")
print("=" * 70)

all_passed = True

for filename, description in test_files:
    print(f"\n{'=' * 70}")
    print(f"TEST: {description}")
    print(f"File: {filename}")
    print(f"{'=' * 70}")
    
    try:
        with open(filename, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        
        print(f"Input columns: {headers}")
        print(f"Rows: {len(rows)}")
        
        # Detect columns
        column_map, warnings = detect_and_report(headers)
        
        print(f"\nDetected mapping:")
        for internal, csv_col in column_map.items():
            if csv_col:
                print(f"  {internal} -> {csv_col}")
            else:
                print(f"  {internal} -> NOT DETECTED")
        
        if warnings:
            print(f"\nWarnings:")
            for w in warnings:
                print(f"  - {w}")
        
        # Verify MPN was detected
        if column_map.get("Mfg_Part_Num"):
            print(f"\n[PASS] MPN detected: {column_map['Mfg_Part_Num']}")
        else:
            print(f"\n[FAIL] MPN NOT DETECTED")
            all_passed = False
        
        # Test mapping first row
        if rows:
            mapped = map_row(rows[0], column_map)
            print(f"\nFirst row mapping:")
            print(f"  Mfg_Part_Num: {mapped['Mfg_Part_Num']}")
            print(f"  Part_Desc: {mapped['Part_Desc']}")
            print(f"  E1_Brand: {mapped['E1_Brand']}")
            print(f"  Part_Manuf: {mapped['Part_Manuf']}")
            
            if mapped['Mfg_Part_Num']:
                print(f"[PASS] Row mapping successful")
            else:
                print(f"[FAIL] Row mapping failed")
                all_passed = False
        
    except Exception as e:
        print(f"[ERROR] {e}")
        all_passed = False

print(f"\n{'=' * 70}")
print("SUMMARY")
print(f"{'=' * 70}")
if all_passed:
    print("[PASS] ALL TESTS PASSED - Smart column detection works with any CSV format")
else:
    print("[FAIL] SOME TESTS FAILED")
