import re

with open('pipeline.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
code = code.replace('import config_appliances as cfg', '''from desc_extraction_provider import DescriptionExtractionProvider
import config_appliances
import config_faucets
import config_fittings''')

# 2. Dynamic config mapping
code = code.replace('''    elif "dishwasher" in part_desc:
        product.classpath = cfg.CLASSPATH
        product.classpath_confidence = 0.95
    else:
        product.classpath = None
        product.classpath_confidence = 0.0''', '''
    if product.classpath:
        category = product.classpath.split(" > ")[1] if " > " in product.classpath else product.classpath
    else:
        category = getattr(product, '_category', 'Unknown')
        
    if "Faucet" in category or "Faucets" in category:
        product._cfg = config_faucets
    elif "Fitting" in category or "Fittings" in category or "Pipe" in category or "Plumbing" in category:
        product._cfg = config_fittings
    else:
        product._cfg = config_appliances''')

# 3. Replace cfg. with product._cfg.
code = code.replace('cfg.', 'product._cfg.')

# 4. Fix Series evidence
code = code.replace('''        if label == "Series" and evidence_found:
            attr.value = evidence_bundle.get("_series")
            attr.status = "verified" if attr.value else "unknown"
        elif label in facts:''', '''        if label == "Series" and evidence_found:
            attr.value = evidence_bundle.get("_series")
            attr.status = "verified" if attr.value else "unknown"
            if evidence_bundle.get("source_url"):
                from models import Evidence
                attr.evidence.append(Evidence(
                    source_url=evidence_bundle.get("source_url"),
                    source_tier=evidence_bundle.get("source_tier", 0)
                ))
                attr.confidence = 100.0 if evidence_bundle.get("source_tier") == 5 else 80.0
        elif label in facts:''')

# 5. Fix fact evidence
code = code.replace('''            attr.value = value
            attr.uom = uom or uom_expected
            attr.evidence.append(ev)
            attr.status = "verified"
        else:''', '''            attr.value = value
            attr.uom = uom or uom_expected
            attr.evidence.append(ev)
            attr.status = "verified"
            if ev and ev.source_tier == 5:
                attr.confidence = 100.0
            elif ev and ev.source_tier >= 3:
                attr.confidence = 80.0
            else:
                attr.confidence = 60.0
        else:''')

# 6. Force high confidence for Tier 5
code = code.replace('''    score = max(0.0, min(1.0, score))
    attr.confidence = score''', '''    score = max(0.0, min(1.0, score))
    if attr.evidence:
        top_tier = max([ev.source_tier for ev in attr.evidence])
        if top_tier == 5:
            score = 1.0
        elif top_tier == 4:
            score = max(score, 0.95)
    attr.confidence = score''')

with open('pipeline.py', 'w', encoding='utf-8') as f:
    f.write(code)
