#!/usr/bin/env python3
# routes フォルダの路線ファイル(*.geojson)から、路線の一覧 routes.json を作る。
# 使い方:route.html と同じフォルダで  python3 make_routes_json.py
# hash  = 中身から作った印。中身が変わると変わるので、ページ側は端末に保存した古いファイルを自動で取り替える。
# km    = 総延長(route_master.length_km)。一覧の「距離順」に使う。
# prefs = 通る都道府県(町村の pref から拾う)。一覧の「都道府県」での絞り込みに使う。
import json, glob, hashlib

PREFS = ['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県',
  '新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県',
  '鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']

items = []
for path in sorted(glob.glob('routes/*.geojson')):
    with open(path, 'rb') as f:
        raw = f.read()
    gj = json.loads(raw.decode('utf-8'))
    feats = gj.get('features', [])
    lines = [x for x in feats if x['properties'].get('kind') == 'line']
    units = [x for x in feats if x['properties'].get('kind') == 'unit']
    if not units:
        print('判定単位が無いので飛ばします:', path)
        continue
    ref = units[0]['properties']['route_ref']
    name = (lines[0] if lines else units[0])['properties'].get('name') or ref
    km = next((x['properties']['length_km'] for x in lines if x['properties'].get('length_km') not in (None, '')), None)
    prefs = sorted({u['properties'].get('pref') for u in units if u['properties'].get('pref')},
                   key=lambda p: PREFS.index(p) if p in PREFS else 99)
    item = {'ref': ref, 'name': name, 'file': path,
            'size_kb': round(len(raw) / 1024),
            'hash': hashlib.sha1(raw).hexdigest()[:12]}
    if km is not None:
        item['km'] = float(km)
    if prefs:
        item['prefs'] = prefs
    items.append(item)

items.sort(key=lambda x: x['ref'])
with open('routes.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
print(len(items), '路線を routes.json に書き出しました')
