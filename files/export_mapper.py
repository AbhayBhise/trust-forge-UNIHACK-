import csv

def map_to_delivery_format(product, original_row, headers):
    """
    Translates a Product object into a flat 252-column dictionary.
    No business logic should exist here.
    """
    mapped = {}
    for h in headers:
        mapped[h] = original_row.get(h, "")

    # Core Identifiers & Names
    mapped["MANUFACTURER_NAME"] = product.manufacturer_name or ""
    mapped["BRAND_NAME"] = product.brand_name or ""
    mapped["Classpath"] = product.classpath or ""
    
    # Descriptions
    for k, v in product.descriptions.items():
        if k in headers:
            mapped[k] = v
            
    # Evidence URL (MFR URL)
    # Grab the first valid evidence URL if MFR URL is not yet populated
    if not mapped.get("MFR URL"):
        for attr in product.attributes:
            if attr.evidence:
                mapped["MFR URL"] = attr.evidence[0].source_url
                break

    # 1-50 Attribute Mapping
    import config_appliances as cfg
    for idx, attr_def in enumerate(cfg.ATTRIBUTES, start=1):
        if idx > 50:
            break
        label = attr_def[0]
        attr = product.get_attr(label)
        mapped[f"ATTRIBUTE_LABEL {idx}"] = label
        mapped[f"ATTRIBUTE_VALUE {idx}"] = str(attr.value) if attr and attr.value is not None else ""
        mapped[f"ATTRIBUTE_UOM {idx}"] = attr.uom if attr and attr.uom else ""
        
    # Clear any leftover attributes from original row if we didn't fill them
    for i in range(len(cfg.ATTRIBUTES) + 1, 51):
        mapped[f"ATTRIBUTE_LABEL {i}"] = ""
        mapped[f"ATTRIBUTE_VALUE {i}"] = ""
        mapped[f"ATTRIBUTE_UOM {i}"] = ""

    return mapped

def write_csv(products, original_rows, headers, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for product, row in zip(products, original_rows):
            mapped = map_to_delivery_format(product, row, headers)
            writer.writerow(mapped)
