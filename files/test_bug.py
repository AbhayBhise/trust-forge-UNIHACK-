import json
from pipeline import build_product
from config_appliances import ATTRIBUTES


class MockProvider:
    """Simple mock provider for testing — returns minimal evidence."""
    def fetch(self, mfg_part_num: str) -> dict:
        return {}
    
    def fetch_with_row(self, mfg_part_num: str, row: dict) -> dict:
        return {
            "_manufacturer_name": "Test Manufacturer",
            "_brand_name": "Test Brand",
            "_series": "",
            "_mfr_url": "test",
            "facts": {},
        }


def prove_bug():
    provider = MockProvider()
    
    # Process PDSH4816AF first
    row_A = {"Mfg_Part_Num": "PDSH4816AF", "Part_Desc": "Dishwasher"}
    p_A = build_product(row_A, provider)
    
    # Process WDTS7024RZ next
    row_B = {"Mfg_Part_Num": "WDTS7024RZ", "Part_Desc": "Dishwasher"}
    p_B = build_product(row_B, provider)
    
    # Process PDSH4816AF again
    p_A2 = build_product(row_A, provider)

    print(f"Product A cycles: {p_A.get_attr('Number of Wash Cycles').value}")
    print(f"Product B cycles: {p_B.get_attr('Number of Wash Cycles').value}")
    print(f"Product A2 cycles: {p_A2.get_attr('Number of Wash Cycles').value}")
    
    print("Product B descriptions:")
    for k, v in p_B.descriptions.items():
        print(f"  {k}: {v}")

    # Inspect the export mapper behavior
    from export_mapper import map_to_delivery_format
    headers = [a[0] for a in ATTRIBUTES]
    
    mapped_B = map_to_delivery_format(p_B, row_B, headers)
    print("Export mapping keys starting with ATTRIBUTE_LABEL:")
    for k, v in mapped_B.items():
        if k.startswith("ATTRIBUTE_LABEL") and v:
            print(f"  {k} = {v}")

prove_bug()
