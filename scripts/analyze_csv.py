import csv
from collections import defaultdict

FILE_PATH = "u:/25.WEBSITE/clone web sirman/clone-web-sirman/sirman_parts_export.csv"

def analyze():
    print(f"[INFO] Analyzing {FILE_PATH}...")
    
    total_rows = 0
    id_counts = defaultdict(int)
    logical_dup_counts = defaultdict(int)
    
    missing_code = 0
    missing_name = 0
    missing_product = 0
    invalid_price = 0
    
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            
            # Check ID uniqueness
            row_id = row.get("id", "").strip()
            id_counts[row_id] += 1
            
            # Check logical duplicates (product_id + code + ref + view_name)
            logical_key = (
                row.get("product_id", "").strip(), 
                row.get("code", "").strip(),
                row.get("ref", "").strip(),
                row.get("view_name", "").strip()
            )
            logical_dup_counts[logical_key] += 1
            
            # Check junk data
            if not row.get("code", "").strip():
                missing_code += 1
            
            # "Part" was the default name in our scraper if missing
            name = row.get("name", "").strip()
            if not name or name.lower() == "part":
                missing_name += 1
                
            if not row.get("product_id", "").strip():
                missing_product += 1
                
            # Check price
            try:
                price = float(row.get("price", 0))
                if price < 0:
                    invalid_price += 1
            except ValueError:
                invalid_price += 1

    duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
    duplicate_logical = {k: v for k, v in logical_dup_counts.items() if v > 1}
    
    print("=== Analysis Results ===")
    print(f"Total Rows Checked: {total_rows}")
    print(f"Duplicate IDs: {sum(v - 1 for v in duplicate_ids.values())} rows")
    print(f"Logical Duplicates (Same Product, Code, Ref, View): {sum(v - 1 for v in duplicate_logical.values())} rows")
    
    print("\n=== Junk Data Checks ===")
    print(f"Missing/Empty Code: {missing_code}")
    print(f"Missing/Default Name ('Part'): {missing_name}")
    print(f"Missing Product ID: {missing_product}")
    print(f"Invalid/Negative Price: {invalid_price}")

if __name__ == "__main__":
    analyze()
