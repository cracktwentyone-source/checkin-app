#!/usr/bin/env python3
# routes フォルダの路線ファイル(*.geojson)から、路線の一覧 routes.json を作る。
# 使い方:route.html と同じフォルダで  python3 make_routes_json.py
# hash は中身から作った印。中身が変わると変わるので、ページ側は端末に保存した古いファイルを自動で取り替える。
import json, os, glob, hashlib

items = []
for path in sorted(glob.glob('routes/*.geojson')):
    with open(path, 'rb') as f:
        raw = f.read()
    gj = json.loads(raw.decode('utf-8'))
    feats = gj.get('features', [])
    line = next((x for x in feats if x['properties'].get('kind') == 'line'), None)
    unit = next((x for x in feats if x['properties'].get('kind') == 'unit'), None)
    if not unit:
        print('判定単位が無いので飛ばします:', path)
        continue
    ref = unit['properties']['route_ref']
    name = (line or unit)['properties'].get('name') or ref
    items.append({'ref': ref, 'name': name, 'file': path,
                  'size_kb': round(len(raw) / 1024),
                  'hash': hashlib.sha1(raw).hexdigest()[:12]})

items.sort(key=lambda x: x['ref'])
with open('routes.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
print(len(items), '路線を routes.json に書き出しました')
