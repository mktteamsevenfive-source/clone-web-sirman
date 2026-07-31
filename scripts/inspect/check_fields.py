import json

d = json.load(open('sirman_catalog_data.json', encoding='utf-8'))
prods = d.get('products', [])

has_barcode = sum(1 for p in prods if p.get('barcode') and p.get('barcode') != p.get('code'))
has_discontinued = sum(1 for p in prods if p.get('discontinued') == True)
total = len(prods)

print(f'Total products: {total}')
print(f'Has unique barcode (not same as code): {has_barcode}')
print(f'Is discontinued = True: {has_discontinued}')
print()

for p in prods[:5]:
    model = p['model'][:40]
    barcode = p.get('barcode', '')
    disc = p.get('discontinued')
    print(f'  model: {model:<40} barcode: {barcode:<20} discontinued: {disc}')
