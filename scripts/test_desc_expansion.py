import sys
sys.path.insert(0, 'files')
from desc_extraction_provider import DescriptionExtractionProvider

p = DescriptionExtractionProvider()

tests = [
    {'Mfg_Part_Num': 'DCB518ASTS06G', 'Part_Desc': 'DCB518ASTS06G 5" 8-Hole Stikit Paper Disc P80 Grit, Aluminum Oxide, 50/Box', 'Part_Manuf': '3M', 'E1_Brand': '3M'},
    {'Mfg_Part_Num': '42-706', 'Part_Desc': '42-706 1/2" NPT Brass Tee Fitting, Forged, 3000 PSI Max Pressure', 'Part_Manuf': 'Matco-Norca', 'E1_Brand': 'Matco-Norca'},
    {'Mfg_Part_Num': '12-2AWG-R', 'Part_Desc': '12/2 AWG UF-B Underground Feeder Wire, Copper, 250 ft Roll, 600V', 'Part_Manuf': 'Southwire', 'E1_Brand': 'Southwire'},
    {'Mfg_Part_Num': '45689-01', 'Part_Desc': '45689-01 Southern Yellow Pine 2x6x12 Pressure Treated Lumber, Ground Contact', 'Part_Manuf': 'Weyerhaeuser', 'E1_Brand': 'Weyerhaeuser'},
    {'Mfg_Part_Num': 'ML-100', 'Part_Desc': 'ML-100 Phillips Head Drywall Screw #8-32 x 1-1/4", Coarse Thread, Torx Drive, 1000ct Box', 'Part_Manuf': 'ITW', 'E1_Brand': 'ITW'},
    {'Mfg_Part_Num': 'DR-2000', 'Part_Desc': 'DR-2000 10" Circular Saw Blade, Carbide, 60T, 5/8" Arbor, Max RPM 5000', 'Part_Manuf': 'Freud', 'E1_Brand': 'Freud'},
]

for row in tests:
    result = p.fetch_from_row(row)
    facts = result.get('facts', {})
    print(f'\n{row["Mfg_Part_Num"]}: {len(facts)} attributes')
    for k, v in facts.items():
        print(f'  {k}: {v[0]}')
