import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def get_dir_stats(path):
    total_size = 0
    total_files = 0
    if not path.exists():
        return 0, 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                total_files += 1
            except Exception:
                pass
    return total_files, total_size

def format_size(bytes_val):
    if bytes_val >= 1024 ** 3:
        return f"{bytes_val / (1024 ** 3):.2f} GB"
    elif bytes_val >= 1024 ** 2:
        return f"{bytes_val / (1024 ** 2):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} Bytes"

print("=== DISK USAGE FOR SCRAPED IMAGES & DATA ===")

# 1. diagram_images folder
diag_cnt, diag_size = get_dir_stats(ROOT_DIR / "diagram_images")
print(f"📁 diagram_images/ (รูปภาพแบบแปลน): {diag_cnt:,} ไฟล์ | ความจุ: {format_size(diag_size)}")

# 2. public/hotspots folder
hs_cnt, hs_size = get_dir_stats(ROOT_DIR / "public" / "hotspots")
print(f"📁 public/hotspots/ (ไฟล์พิกัด JSON): {hs_cnt:,} ไฟล์ | ความจุ: {format_size(hs_size)}")

# 3. public folder overall
pub_cnt, pub_size = get_dir_stats(ROOT_DIR / "public")
print(f"📁 public/ (รวมไฟล์ทั้งหมดใน public): {pub_cnt:,} ไฟล์ | ความจุ: {format_size(pub_size)}")

# 4. JSON & DB Files
db_size = os.path.getsize(ROOT_DIR / "sirman_catalog.db") if (ROOT_DIR / "sirman_catalog.db").exists() else 0
cat_json_size = os.path.getsize(ROOT_DIR / "sirman_catalog_data.json") if (ROOT_DIR / "sirman_catalog_data.json").exists() else 0
parts_json_size = os.path.getsize(ROOT_DIR / "sirman_parts.json") if (ROOT_DIR / "sirman_parts.json").exists() else 0

print(f"\n🗄️ sirman_catalog.db (SQLite Database) : {format_size(db_size)}")
print(f"📄 sirman_catalog_data.json              : {format_size(cat_json_size)}")
print(f"📄 sirman_parts.json                     : {format_size(parts_json_size)}")

total_all_bytes = diag_size + pub_size + db_size + cat_json_size + parts_json_size
print(f"\n💾 ความจุรวมทั้งหมดของข้อมูลและรูปภาพในโปรเจกต์: {format_size(total_all_bytes)}")
