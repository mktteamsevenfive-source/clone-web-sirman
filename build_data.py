import json
import re
import html
from pathlib import Path

BASE_DIR = Path(__file__).parent
PARTS_FILE = BASE_DIR / "sirman_parts.json"
OUTPUT_FILE = BASE_DIR / "sirman_catalog_data.json"

print(f"Reading {PARTS_FILE}...")
with open(PARTS_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

categories_map = raw_data.get("categories", {})

icon_map = {
    "microwaves-ovens": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M15 25 H85 V75 H15 Z M22 32 H65 V68 H22 Z M72 32 H78 V36 H72 Z M72 42 H78 V46 H72 Z M75 58 A5 5 0 1 0 75 68 A5 5 0 1 0 75 58 Z M28 42 Q 35 35 42 42 T 56 42" stroke="currentColor" stroke-width="3" fill="none"/><path d="M28 54 Q 35 47 42 54 T 56 54" stroke="currentColor" stroke-width="3" fill="none"/></svg>',
    "snack-and-pizza": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M20 70 L50 25 L80 70 Z M20 74 H80 V78 H20 Z M38 52 A5 5 0 1 0 38 62 A5 5 0 1 0 38 52 Z M58 45 A4 4 0 1 0 58 53 A4 4 0 1 0 58 45 Z M52 60 A4 4 0 1 0 52 68 A4 4 0 1 0 52 60 Z"/></svg>',
    "consumables-and-accessories": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M50 20 A30 30 0 1 0 50 80 A30 30 0 1 0 50 20 Z M50 35 A15 15 0 1 1 50 65 A15 15 0 1 1 50 35 Z"/><circle cx="75" cy="45" r="10"/></svg>',
    "laundry": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M22 20 H78 V80 H22 Z M50 35 A18 18 0 1 0 50 71 A18 18 0 1 0 50 35 Z M50 43 A10 10 0 1 1 50 63 A10 10 0 1 1 50 43 Z"/><circle cx="32" cy="28" r="3"/><circle cx="42" cy="28" r="3"/></svg>',
    "food-processors": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M50 25 C30 25 18 42 18 55 H82 C82 42 70 25 50 25 Z M47 15 H53 V25 H47 Z M15 58 H85 V64 H15 Z M22 68 H78 V72 H22 Z"/></svg>',
    "cooking-machines": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M40 15 C40 15 42 22 38 27 M50 12 C50 12 52 20 48 26 M60 15 C60 15 62 22 58 27" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none"/><path d="M20 40 H80 V46 H20 Z M24 48 H76 V65 C76 73.3 69.3 80 61 80 H39 C30.7 80 24 73.3 24 65 Z M15 48 H21 V56 H15 Z M79 48 H85 V56 H79 Z"/></svg>',
    "bar-machines": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M70,30 H25 C22.2,30 20,32.2 20,35 V60 C20,68.3 26.7,75 35,75 H50 C58.3,75 65,68.3 65,60 V55 H70 C76.6,55 82,49.6 82,43 C82,35.8 76.6,30 70,30 Z M70,47 H65 V38 H70 C72.8,38 75,40.2 75,43 C75,45.8 72.8,47 70,47 Z M15,82 H75 V88 H15 Z"/></svg>',
    "packaging-machines": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M25 30 H75 V80 H25 Z M35 20 H65 V28 H35 Z M35 45 A6 6 0 1 0 35 57 A6 6 0 1 0 35 45 Z M55 45 A6 6 0 1 0 55 57 A6 6 0 1 0 55 45 Z M45 62 A6 6 0 1 0 45 74 A6 6 0 1 0 45 62 Z"/></svg>',
    "scales": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M35 25 H65 L78 78 H22 Z"/><text x="32" y="60" font-family="Outfit, sans-serif" font-size="22" font-weight="800" fill="#FFFFFF">KG</text></svg>',
    "ozone-generators": '<svg viewBox="0 0 100 100" fill="currentColor"><text x="15" y="68" font-family="Outfit, sans-serif" font-size="52" font-weight="800">O</text><text x="56" y="76" font-family="Outfit, sans-serif" font-size="34" font-weight="800">3</text><circle cx="80" cy="35" r="2"/><circle cx="88" cy="45" r="3"/><circle cx="75" cy="55" r="1.5"/></svg>',
    "slicers": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M75 22 A28 28 0 0 0 47 50 A28 28 0 0 0 75 78 V22 Z M60 22 A28 28 0 0 0 32 50 A28 28 0 0 0 60 78 V22 Z M45 22 A28 28 0 0 0 17 50 A28 28 0 0 0 45 78 V22 Z"/></svg>',
    "dishwashers": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M70 30 H25 C22.2 30 20 32.2 20 35 V60 C20 68.3 26.7 75 35 75 H50 C58.3 75 65 68.3 65 60 V55 H70 C76.6 55 82 49.6 82 43 C82 35.8 76.6 30 70 30 Z M70 47 H65 V38 H70 C72.8 38 75 40.2 75 43 C75 45.8 72.8 47 70 47 Z M15 82 H75 V88 H15 Z"/><path d="M25 22 Q 45 15 65 22" stroke="currentColor" stroke-width="3" fill="none"/></svg>',
    "meat-processors": '<svg viewBox="0 0 100 100" fill="currentColor"><path d="M35 25 C20 25 15 40 22 58 C28 73 50 82 72 75 C85 70 88 52 78 38 C68 24 50 25 35 25 Z M42 42 A8 8 0 1 1 42 58 A8 8 0 1 1 42 42 Z"/></svg>'
}

categories = []
products = []

for cat_name, cat_data in categories_map.items():
    slug = re.sub(r'[^a-z0-9]+', '-', cat_name.lower()).strip('-')
    cat_id = slug
    prods = cat_data.get("products", [])
    
    categories.append({
        "id": cat_id,
        "sirman_id": cat_data.get("id"),
        "name": cat_name,
        "count": len(prods),
        "icon": icon_map.get(slug, icon_map["food-processors"])
    })
    
    for p in prods:
        p_name = p.get("name", "Unknown")
        p_id = p.get("id")
        raw = p.get("raw", {})
        exploded_pdf = raw.get("firstExplodedViewPdfName", "")
        exploded_id = raw.get("firstExplodedViewId", "")
        
        # Clean parts list
        parts_list = []
        seen_part_keys = set()
        for part in p.get("parts", []):
            part_id = str(part.get("id", "")).strip()
            if not part_id:
                continue
                
            # Prioritize English names (i18n['en'], nameEn, etc.)
            p_name_en = (
                part.get("i18n", {}).get("en") or 
                part.get("nameEn") or 
                part.get("name") or 
                part.get("i18n", {}).get("it") or 
                part_id
            ).strip()
            price = part.get("price", 0)
            try:
                price_float = float(price)
            except (ValueError, TypeError):
                price_float = 0.0
                
            part_obj = {
                "code": part_id,
                "name": p_name_en,
                "price": round(price_float, 2),
                "stock": part.get("dispTot", 0),
                "ref": str(part.get("explodedViewRef", "")).strip(),
                "view_name": part.get("_view_name", "")
            }
            
            # Avoid exact duplicates within same product
            dedup_key = f"{part_id}_{part_obj['ref']}"
            if dedup_key not in seen_part_keys:
                seen_part_keys.add(dedup_key)
                parts_list.append(part_obj)
            
        code_str = f"SIR-{cat_id[:3].upper()}-{p_id}"
        serial_str = f"SN-{p_id:04d}"
        
        products.append({
            "id": p_id,
            "code": code_str,
            "model": p_name,
            "serial": serial_str,
            "category": cat_name,
            "categoryId": cat_id,
            "description": f"Sirman {p_name} ({cat_name}). Spare parts catalog & exploded view.",
            "status": "in_production",
            "pdfName": exploded_pdf,
            "explodedViewId": exploded_id,
            "hasExplodedView": len(parts_list) > 0,
            "partsCount": len(parts_list),
            "parts": parts_list
        })

output = {
    "categories": categories,
    "products": products
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    json.dump(output, out, indent=2, ensure_ascii=False)

print(f"Successfully generated {OUTPUT_FILE}!")
print(f"Categories: {len(categories)}")
print(f"Products: {len(products)}")
print(f"Total parts across all products: {sum(len(p['parts']) for p in products)}")
