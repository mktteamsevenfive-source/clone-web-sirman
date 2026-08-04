"""
deduplicate_supabase_images.py
================================
1. Lists all files in Supabase Storage 'diagram_images' bucket
2. Group files by clean base name (e.g. 'pbpf8mm_tc42gol')
3. Retains ONE clean primary filename ('pbpf8mm_tc42gol.png') per diagram
4. Deletes duplicate alias files (e.g. '*.pdf.png', extra uppercase/lowercase copies) via Bulk Delete API
5. Reports total storage freed
"""
import json
import re
import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUPABASE_URL     = 'https://ofrerwyoasklgsejlbzr.supabase.co'
SUPABASE_SERVICE = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTM2NjY1NSwiZXhwIjoyMTAwOTQyNjU1fQ.shN-wvqCOZi1GtPO3rwCHF51OQ0hf23E_GVn9bt3bHQ'
SUP_HEADERS = {'apikey': SUPABASE_SERVICE, 'Authorization': 'Bearer ' + SUPABASE_SERVICE}

def list_all_supabase_files() -> list:
    all_files = []
    offset = 0
    while True:
        url = f'{SUPABASE_URL}/storage/v1/object/list/diagram_images'
        r = requests.post(url, headers=SUP_HEADERS,
                          json={'limit': 1000, 'offset': offset, 'prefix': '',
                                'sortBy': {'column': 'name', 'order': 'asc'}}, timeout=30)
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        all_files.extend(items)
        if len(items) < 1000:
            break
        offset += 1000
    return all_files

def delete_files_bulk(filenames: list) -> int:
    if not filenames:
        return 0
    deleted_count = 0
    # Supabase Storage bulk delete accepts batches of up to 100
    for i in range(0, len(filenames), 100):
        batch = filenames[i:i+100]
        url = f'{SUPABASE_URL}/storage/v1/object/diagram_images'
        r = requests.delete(url, headers=SUP_HEADERS, json={'prefixes': batch}, timeout=30)
        if r.status_code in (200, 204):
            deleted_count += len(batch)
        else:
            print(f"  [DELETE ERR] Batch status {r.status_code}: {r.text[:100]}")
    return deleted_count

def main():
    print("=" * 65)
    print("  SUPABASE STORAGE DIAGRAM IMAGES DEDUPLICATION")
    print("=" * 65)

    print("[1] Fetching complete file list from Supabase Storage...")
    files = list_all_supabase_files()
    total_count = len(files)
    total_bytes = sum(f.get('metadata', {}).get('size', 0) for f in files if isinstance(f, dict))
    total_mb = total_bytes / (1024 * 1024)

    print(f"  Total current files: {total_count}")
    print(f"  Total current storage size: {total_mb:.2f} MB")

    # Group files by core identity key
    # e.g. "pbpf8mm_tc42gol.pdf.png" -> key = "pbpf8mm_tc42gol"
    groups = {}
    for item in files:
        name = item.get('name', '')
        if not name:
            continue

        size = item.get('metadata', {}).get('size', 0)

        # Normalize key: strip .pdf.png, .png, .jpg, lower case
        clean_key = re.sub(r'(\.pdf)?\.png$', '', name, flags=re.IGNORECASE).strip().lower()
        clean_key = clean_key.replace(' ', '_')

        if clean_key not in groups:
            groups[clean_key] = []
        groups[clean_key].append({'name': name, 'size': size})

    to_keep = []
    to_delete = []

    for key, items in groups.items():
        if len(items) == 1:
            to_keep.append(items[0]['name'])
        else:
            # Pick best single file to KEEP:
            # Prefer clean '.png' over '.pdf.png'
            best = None
            for it in items:
                fn = it['name']
                if not fn.endswith('.pdf.png') and fn.endswith('.png'):
                    best = fn
                    break

            if not best:
                best = items[0]['name']

            to_keep.append(best)
            for it in items:
                if it['name'] != best:
                    to_delete.append(it['name'])

    freed_bytes = 0
    file_map = {f['name']: f.get('metadata', {}).get('size', 0) for f in files}
    for fn in to_delete:
        freed_bytes += file_map.get(fn, 0)
    freed_mb = freed_bytes / (1024 * 1024)

    print(f"\n[2] Analysis Results:")
    print(f"  Files to KEEP: {len(to_keep)}")
    print(f"  Redundant alias files to DELETE: {len(to_delete)}")
    print(f"  Estimated storage to be FREED: {freed_mb:.2f} MB")

    if not to_delete:
        print("\nNo duplicate alias files found to delete!")
        return

    print(f"\n[3] Deleting {len(to_delete)} duplicate alias files from Supabase Storage...")
    deleted = delete_files_bulk(to_delete)

    print("\n" + "=" * 65)
    print(f"  DEDUPLICATION COMPLETE! ✅")
    print(f"  Successfully deleted: {deleted} files")
    print(f"  Storage freed: {freed_mb:.2f} MB")
    print(f"  New estimated Storage Size: {(total_mb - freed_mb):.2f} MB")
    print("=" * 65)

if __name__ == "__main__":
    main()
