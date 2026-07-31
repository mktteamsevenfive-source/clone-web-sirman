import json
import sqlite3
import sys
import os
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_FILE = ROOT_DIR / "sirman_catalog_data.json"
PARTS_FILE = ROOT_DIR / "sirman_parts.json"
DB_FILE = ROOT_DIR / "sirman_catalog.db"
HOTSPOTS_DIR = ROOT_DIR / "public" / "hotspots"

def render_progress_bar(percent, width=30):
    filled = int(width * percent // 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percent:5.1f}%"

def show():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("==================================================================")
    print("                SIRMAN SCRAPER LIVE PROGRESS DASHBOARD            ")
    print("==================================================================")

    # Products & Categories
    total_products = 0
    total_categories = 0
    if CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE, encoding="utf-8") as f:
                d = json.load(f)
            total_categories = len(d.get("categories", []))
            total_products = len(d.get("products", []))
        except Exception:
            pass

    # Parts
    total_parts = 0
    if PARTS_FILE.exists():
        try:
            with open(PARTS_FILE, encoding="utf-8") as f:
                d = json.load(f)
            total_parts = len(d.get("all_parts", []))
        except Exception:
            pass

    # SQLite
    sqlite_prods = 0
    sqlite_parts = 0
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            sqlite_prods = c.execute("SELECT count(*) FROM products").fetchone()[0]
            sqlite_parts = c.execute("SELECT count(*) FROM parts").fetchone()[0]
            conn.close()
        except Exception:
            pass

    # Hotspots
    hotspot_files = len(list(HOTSPOTS_DIR.glob("*.json"))) if HOTSPOTS_DIR.exists() else 0

    print(f"\n📦 PRODUCTS SCRAPED  : {total_products:,} items")
    print(f"📁 CATEGORIES LISTED  : {total_categories:,} main categories")
    print(f"🔩 PARTS SCRAPED      : {total_parts:,} individual parts")
    print(f"🎯 DIAGRAM HOTSPOTS   : {hotspot_files:,} JSON files downloaded")
    print(f"🗄️ SQLITE DATABASE    : {sqlite_prods:,} products / {sqlite_parts:,} parts synced")

    print("\n------------------------------------------------------------------")
    # Target estimate (e.g. 829 products scraped, target estimate 1282 categories scanned)
    cat_pct = min(100.0, (total_categories / 13) * 100) if total_categories else 0
    print(f"Categories Scraped  : {render_progress_bar(cat_pct)} ({total_categories}/13 categories)")
    
    parts_pct = min(100.0, (total_parts / 70000) * 100)
    print(f"Parts Target (~70k) : {render_progress_bar(parts_pct)} ({total_parts:,}/70,000 parts)")
    
    hotspots_pct = min(100.0, (hotspot_files / 536) * 100)
    print(f"Hotspot Blueprints  : {render_progress_bar(hotspots_pct)} ({hotspot_files}/536 diagrams)")

    print("==================================================================")

if __name__ == "__main__":
    show()
