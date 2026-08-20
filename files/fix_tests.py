import os

# fix test_robustness.py
with open('test_robustness.py', 'r') as f:
    code = f.read()

if 'import config_appliances' not in code:
    code = code.replace('def setUp(self):', 'def setUp(self):\n        import config_appliances\n')
if 'self.product._cfg = config_appliances' not in code:
    code = code.replace('attributes=attrs\n        )', 'attributes=attrs\n        )\n        self.product._cfg = config_appliances')

with open('test_robustness.py', 'w') as f:
    f.write(code)


# fix test_validation.py
with open('test_validation.py', 'r') as f:
    code = f.read()

code = code.replace('_score_confidence(attr)', '_score_confidence(attr, self.product)')
if 'import config_appliances' not in code:
    code = code.replace('self.product = Product("123", "Test")', 'self.product = Product("123", "Test")\n        import config_appliances\n        self.product._cfg = config_appliances')

with open('test_validation.py', 'w') as f:
    f.write(code)

print("Tests patched successfully")
