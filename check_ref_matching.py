import json

d = json.load(open('public/hotspots/apollo_y15.json', encoding='utf-8'))
for c in d.get('clickableElements', []):
    item_id = c.get('itemId')
    matched = c.get('matchedItemId')
    text = ""
    content = c.get('content', '')
    if '<text' in content:
        text = content.split('>')[-2].split('<')[0]
    print(f"itemId: {str(item_id):<8} | matchedItemId: {str(matched):<8} | SVG Text: {text}")
