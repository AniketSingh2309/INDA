import json, os, urllib.request, time
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "maps"))
os.makedirs(OUT, exist_ok=True)
UA = "GameInventoryDashboard/1.0 (educational game project)"

SOURCES = [
 "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/india.geojson",
 "https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States",
 "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson",
 "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/india/india-states.json",
]
def get(u):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(5*(a+1)); continue
            print("http", e.code, u); return None
        except Exception as e:
            print("err", e, u); return None
    return None

gj = None; src = None
for u in SOURCES:
    raw = get(u)
    if not raw: continue
    try:
        d = json.loads(raw)
    except Exception as e:
        print("not json", u, e); continue
    if d.get("type") == "FeatureCollection" and d.get("features"):
        gj = d; src = u; break
    if d.get("type") == "Topology":
        print("topojson (skip, need converter):", u); continue
if not gj:
    print("NO SOURCE WORKED"); raise SystemExit(1)
print("using", src, "features:", len(gj["features"]))

def rnd(c): return [round(c[0], 2), round(c[1], 2)]
def dedupe(ring):
    out = []
    for p in ring:
        if not out or out[-1] != p: out.append(p)
    return out
def simp_ring(ring):
    return dedupe([rnd(p) for p in ring])

def ring_area(ring):
    a = 0.0
    for i in range(len(ring)-1):
        a += ring[i][0]*ring[i+1][1] - ring[i+1][0]*ring[i][1]
    return abs(a)/2.0

feats = []
for f in gj["features"]:
    g = f.get("geometry") or {}
    t = g.get("type"); coords = g.get("coordinates")
    if not coords: continue
    name = ""
    for k in ("ST_NM","NAME_1","name","State_Name","st_nm","STATE"):
        if f.get("properties", {}).get(k): name = f["properties"][k]; break
    polys = []
    if t == "Polygon": polys = [coords]
    elif t == "MultiPolygon": polys = coords
    newpolys = []
    for poly in polys:
        newrings = []
        for ri, ring in enumerate(poly):
            sr = simp_ring(ring)
            if len(sr) < 4: continue
            if ri == 0 and ring_area(sr) < 0.01:  # drop tiny outer islands
                continue
            newrings.append(sr)
        if newrings: newpolys.append(newrings)
    if not newpolys: continue
    feats.append({"type":"Feature","properties":{"name":name},
                  "geometry":{"type":"MultiPolygon","coordinates":newpolys}})

fc = {"type":"FeatureCollection","features":feats}
path = os.path.join(OUT, "india.min.json")
json.dump(fc, open(path, "w"), separators=(",", ":"))
print("wrote", path, round(os.path.getsize(path)/1024, 1), "KB |", len(feats), "features")
