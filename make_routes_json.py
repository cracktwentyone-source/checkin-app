#!/usr/bin/env python3
# routes フォルダの路線ファイル(*.geojson)から、路線の一覧 routes.json を作る。
# 使い方:route.html と同じフォルダで  python3 make_routes_json.py
import json, os, glob

items = []
for path in sorted(glob.glob('routes/*.geojson')):
    with open(path, encoding='utf-8') as f:
        gj = json.load(f)
    feats = gj.get('features', [])
    line = next((x for x in feats if x['properties'].get('kind') == 'line'), None)
    unit = next((x for x in feats if x['properties'].get('kind') == 'unit'), None)
    if not unit:
        print('判定単位が無いので飛ばします:', path)
        continue
    ref = unit['properties']['route_ref']
    name = (line or unit)['properties'].get('name') or ref
    items.append({'ref': ref, 'name': name, 'file': path,
                  'size_kb': round(os.path.getsize(path) / 1024)})

items.sort(key=lambda x: x['ref'])
with open('routes.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
print(len(items), '路線を routes.json に書き出しました')
