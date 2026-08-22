"""Debug desc extraction patterns on actual descriptions"""
import sys
import re
sys.path.insert(0, 'files')
from desc_extraction_provider import (
    DIM_PATTERNS, _extract_single, DIAMETER_PATTERN, ARBOR_PATTERN,
    _extract_grit, _extract_quantity, _classify_category
)

descriptions = [
    ("DCB518ASTS06G", "DCB518ASTS06G Diablo 1/2\"x18\" - Sanding Belt 6pc"),
    ("3MABR-7100075678", "3M 775L Stikit Film P150 - Cubitron II 50 Disc/Box"),
    ("9A-570-240", "9A-570-240 Abranet 2.75x30"),
    ("DBD090094101F", "DBD090094101F Diablo 9\" - Metal Cut-Off Disc"),
    ("DBDS12125A01F", "DBDS12125A01F Diablo 12\" - Steel Demon Metal Cut-Off Disc"),
    ("49-94-0013", "49-94-0013 Milw 5\"x.045\"x7/8\" Metal Cut Off Disc"),
    ("42-706", "42-706 1/2\" NPT Brass Tee Fitting, Forged, 3000 PSI"),
    ("12-2AWG-R", "12/2 AWG UF-B Underground Feeder Wire, Copper, 250 ft Roll, 600V"),
]

for mpn, desc in descriptions:
    # Strip MPN
    desc_clean = desc
    if mpn and mpn in desc:
        desc_clean = desc.replace(mpn, '', 1).strip(' -')
    
    print(f"\n{'='*60}")
    print(f"MPN: {mpn}")
    print(f"Original: {desc}")
    print(f"Cleaned:  {desc_clean}")
    print(f"Category: {_classify_category(desc_clean.lower())}")
    
    # Test each pattern
    for pat, attr_label, uom in DIM_PATTERNS:
        m = pat.search(desc_clean)
        if m:
            print(f"  DIM: {attr_label} = {m.group(0)} (uom={uom})")
            break
    
    grit = _extract_grit(desc_clean)
    if grit:
        print(f"  GRIT: {grit}")
    
    qty = _extract_quantity(desc_clean)
    if qty:
        print(f"  QTY: {qty}")
    
    arbor = _extract_single(ARBOR_PATTERN, desc_clean)
    if arbor:
        print(f"  ARBOR: {arbor}")
