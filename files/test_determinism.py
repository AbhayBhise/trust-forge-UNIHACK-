import unittest
import json
import time
from pipeline import build_product
from eval import load_input_rows, deduplicate


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


class TestDeterminismAndPerformance(unittest.TestCase):
    def test_aba(self):
        provider = MockProvider()
        row_A = {"Mfg_Part_Num": "PDSH4816AF", "Part_Desc": "Dishwasher"}
        row_B = {"Mfg_Part_Num": "WDTS7024RZ", "Part_Desc": "Dishwasher"}
        
        out_A1 = build_product(row_A, provider).to_dict()
        out_B = build_product(row_B, provider).to_dict()
        out_A2 = build_product(row_A, provider).to_dict()
        
        self.assertEqual(json.dumps(out_A1, sort_keys=True), json.dumps(out_A2, sort_keys=True), "ABA test failed: State leaked between products!")

    def test_determinism(self):
        provider = MockProvider()
        rows = load_input_rows()
        unique_rows, _ = deduplicate(rows)
        
        from export_mapper import map_to_delivery_format
        import config_appliances as cfg
        headers = [a[0] for a in cfg.ATTRIBUTES]
        
        # Run 10 times
        outputs = []
        for _ in range(10):
            batch_out = []
            for r in unique_rows:
                p = build_product(r, provider)
                mapped = map_to_delivery_format(p, r, headers)
                batch_out.append(mapped)
            outputs.append(json.dumps(batch_out, sort_keys=True))
            
        # All 10 outputs should be byte-for-byte identical
        first_output = outputs[0]
        for i, output in enumerate(outputs[1:], 1):
            self.assertEqual(first_output, output, f"Run {i+1} diverged from run 1!")
            
    def test_performance(self):
        provider = MockProvider()
        rows = load_input_rows()
        unique_rows, _ = deduplicate(rows)
        
        start_time = time.time()
        iterations = 50
        for _ in range(iterations):
            for r in unique_rows:
                build_product(r, provider)
        end_time = time.time()
        
        total_time = end_time - start_time
        total_products = len(unique_rows) * iterations
        time_per_product = total_time / total_products
        
        print(f"\n--- Performance Baseline ---")
        print(f"Time per product: {time_per_product*1000:.2f} ms")
        print(f"Throughput: {1/time_per_product:.2f} products/sec")
        print("----------------------------\n")
        self.assertTrue(time_per_product < 1.0) # should be fast


if __name__ == "__main__":
    unittest.main()
