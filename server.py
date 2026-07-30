"""
SIRMAN CATALOG SQLITE API & WEB SERVER
======================================
Serves SQLite DB endpoints & static website files on port 8000.
Endpoints:
- GET /api/categories
- GET /api/products?category={id}&page={p}&limit={l}&q={search}
- GET /api/products/{id}
- GET /api/stats
- Static files: index.html, styles.css, app.js, diagram_images/*
"""

import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "sirman_catalog.db"
PORT = 8000


def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class SirmanCatalogHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # Handle API Routes
        if path.startswith("/api/"):
            return self.handle_api_request(path, params)

        # Default static file handler
        return super().do_GET()

    def handle_api_request(self, path, params):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # GET /api/categories
            if path == "/api/categories":
                cursor.execute("SELECT id, sirman_id, name, count, icon FROM categories ORDER BY name ASC;")
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json_response(rows)

            # GET /api/stats
            if path == "/api/stats":
                cursor.execute("SELECT COUNT(*) as cats FROM categories;")
                cats_cnt = cursor.fetchone()["cats"]
                cursor.execute("SELECT COUNT(*) as prods FROM products;")
                prods_cnt = cursor.fetchone()["prods"]
                cursor.execute("SELECT COUNT(*) as parts FROM parts;")
                parts_cnt = cursor.fetchone()["parts"]

                return self.send_json_response({
                    "categories": cats_cnt,
                    "products": prods_cnt,
                    "parts": parts_cnt,
                    "db_size_mb": round(DB_FILE.stat().st_size / (1024 * 1024), 2)
                })

            # GET /api/products
            if path == "/api/products":
                cat_id = params.get("category", [""])[0].strip()
                search_q = params.get("q", [""])[0].strip()
                page = int(params.get("page", [1])[0])
                limit = int(params.get("limit", [20])[0])
                page = max(1, page)
                limit = min(max(1, limit), 1000)
                offset = (page - 1) * limit

                query = "SELECT * FROM products WHERE 1=1"
                args = []

                if cat_id:
                    query += " AND category_id = ?"
                    args.append(cat_id)

                if search_q:
                    query += " AND (model LIKE ? OR code LIKE ? OR description LIKE ?)"
                    wildcard = f"%{search_q}%"
                    args.extend([wildcard, wildcard, wildcard])

                # Count total matching products
                count_query = f"SELECT COUNT(*) as total FROM ({query})"
                cursor.execute(count_query, args)
                total_items = cursor.fetchone()["total"]
                total_pages = math.ceil(total_items / limit) if total_items > 0 else 1

                # Select paginated products
                query += " ORDER BY model ASC LIMIT ? OFFSET ?"
                args.extend([limit, offset])

                cursor.execute(query, args)
                rows = [dict(r) for r in cursor.fetchall()]
                formatted_rows = []
                for r in rows:
                    item = dict(r)
                    item["categoryId"] = item.get("category_id")
                    item["categoryName"] = item.get("category_name")
                    item["category"] = item.get("category_name")
                    item["pdfName"] = item.get("pdf_name")
                    item["explodedViewId"] = item.get("exploded_view_id")
                    item["partsCount"] = item.get("parts_count", 0)
                    formatted_rows.append(item)

                return self.send_json_response({
                    "page": page,
                    "limit": limit,
                    "total": total_items,
                    "totalPages": total_pages,
                    "products": formatted_rows
                })

            # GET /api/products/{id}
            prod_match = re.match(r"^/api/products/(\d+)$", path)
            if prod_match:
                p_id = int(prod_match.group(1))
                cursor.execute("SELECT * FROM products WHERE id = ?", (p_id,))
                p_row = cursor.fetchone()
                if not p_row:
                    return self.send_error_response(404, "Product not found")

                prod = dict(p_row)
                prod["categoryId"] = prod.get("category_id")
                prod["categoryName"] = prod.get("category_name")
                prod["category"] = prod.get("category_name")
                prod["pdfName"] = prod.get("pdf_name")
                prod["explodedViewId"] = prod.get("exploded_view_id")
                prod["partsCount"] = prod.get("parts_count", 0)

                # Fetch parts for product
                cursor.execute("""
                    SELECT code, name, price, stock, ref, view_name 
                    FROM parts 
                    WHERE product_id = ? 
                    ORDER BY ref ASC, code ASC
                """, (p_id,))
                parts = [dict(r) for r in cursor.fetchall()]
                prod["parts"] = parts

                return self.send_json_response(prod)

            conn.close()
            return self.send_error_response(404, "Endpoint not found")

        except Exception as err:
            import traceback
            traceback.print_exc()
            return self.send_error_response(500, f"Server Error: {err}")

    def send_json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_response(self, status, message):
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server():
    print("=" * 65)
    print(f"  SIRMAN SQLITE API & WEB SERVER RUNNING ON PORT {PORT}")
    print(f"  URL: http://localhost:{PORT}")
    print("=" * 65)
    server = HTTPServer(("0.0.0.0", PORT), SirmanCatalogHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
