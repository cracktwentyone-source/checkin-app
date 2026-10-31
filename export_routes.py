#!/usr/bin/env python3
# 路線ファイルをまとめて書き出す(テンプレの ⑧⑨ をまとめてやるもの)。
# road_app を ogr2ogr で1回だけ読み出し、路線ごとに routes/rXX_NNN.geojson に分けて保存し、最後に routes.json を作り直す。
# 中身が変わっていないファイルは書き換えない(GitHub Desktop に余計な変更が出ないように)。
#
# 使い方(route.html と同じフォルダで):
#   python3 export_routes.py --pc 00                       国道を全部
#   python3 export_routes.py --pc 00 --from 1 --to 100     国道1〜100号
#   python3 export_routes.py --pc 06 --nums 9,17,49        山形県道9・17・49号
#   python3 export_routes.py --all                         作った路線を全部
#   --db mitz(DB名。省略すると mitz)
import argparse, json, os, subprocess, sys, tempfile

ap = argparse.ArgumentParser(description='路線ファイルをまとめて書き出す')
ap.add_argument('--pc', help='都道府県コード。国道は 00、山形県道は 06')
ap.add_argument('--from', dest='frm', type=int, help='番号の範囲の始め')
ap.add_argument('--to', type=int, help='番号の範囲の終わり')
ap.add_argument('--nums', help='番号をカンマ区切りで(例 9,17,49)')
ap.add_argument('--all', action='store_true', help='作った路線を全部')
ap.add_argument('--db', default='mitz')
a = ap.parse_args()
if not a.all and not a.pc:
    sys.exit('--pc(国道は 00)か --all を指定してください')
pc = None if a.all else a.pc.zfill(2)
nums = {int(x) for x in a.nums.replace(' ', '').split(',') if x} if a.nums else None

def wanted(ref):
    p, _, n = ref.partition('-')
    if pc is not None and p != pc: return False
    try: n = int(n)
    except ValueError: return False
    if a.frm is not None and n < a.frm: return False
    if a.to is not None and n > a.to: return False
    if nums is not None and n not in nums: return False
    return True

os.makedirs('routes', exist_ok=True)
tmp = os.path.join(tempfile.mkdtemp(), 'road_app.geojsonl')
cmd = ['ogr2ogr', '-f', 'GeoJSONSeq', tmp, f'PG:dbname={a.db}', 'roadshow.road_app',
       '-t_srs', 'EPSG:4326', '-lco', 'COORDINATE_PRECISION=6']
if pc is not None:
    cmd += ['-where', f"route_ref LIKE '{pc}-%'"]
print('データベースから読み出しています(路線が多いと数分かかります)…')
r = subprocess.run(cmd)
if r.returncode != 0:
    sys.exit('ogr2ogr でエラーになりました')

groups = {}
with open(tmp, encoding='utf-8') as f:
    for line in f:
        line = line.strip().lstrip('\x1e')
        if not line: continue
        ft = json.loads(line)
        ref = (ft.get('properties') or {}).get('route_ref')
        if not ref or not wanted(ref): continue
        groups.setdefault(ref, []).append(ft)

def fname(ref):
    p, _, n = ref.partition('-')
    n = int(n)
    return f'routes/r{p}_{n:03d}.geojson'

new = same = 0
for ref in sorted(groups):
    feats = groups[ref]
    if not any(ft['properties'].get('kind') == 'unit' for ft in feats):
        print('町村が無いので飛ばします:', ref); continue
    out = json.dumps({'type': 'FeatureCollection', 'name': 'road_app', 'features': feats},
                     ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    path = fname(ref)
    if os.path.exists(path) and open(path, 'rb').read() == out:
        same += 1; continue
    with open(path, 'wb') as f: f.write(out)
    new += 1
print(f'{len(groups)} 路線を読み出しました(書き換え {new}、変わらず {same})')
os.remove(tmp)

r = subprocess.run([sys.executable, 'make_routes_json.py'])
sys.exit(r.returncode)
