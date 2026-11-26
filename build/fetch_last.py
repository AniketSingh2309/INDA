import json, os, urllib.request, urllib.parse, time

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
manifest = json.load(open(MAN)) if os.path.exists(MAN) else {}

# multiple candidate titles per stubborn key
CANDIDATES = {
    "fal": ["FN FAL", "FN_FAL"],
    "cheytac": ["CheyTac Intervention", "CheyTac M200"],
    "pkm": ["PK machine gun"],
    "rem870": ["Remington Model 870", "Remington 870"],
    "benelli": ["Benelli M4", "Benelli M4 Super 90"],
    "carlg": ["Carl Gustaf 8.4 cm recoilless rifle", "Carl-Gustaf 8.4 cm recoilless rifle", "Carl Gustaf recoilless rifle"],
}
UA = "GameInventoryDashboard/1.0 (educational game project)"

def get(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(4 * (attempt + 1)); continue
            raise
    raise RuntimeError("429 giveup")

def rest_thumb(title):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    try:
        data = json.loads(get(url))
    except Exception:
        return None
    for k in ("originalimage", "thumbnail"):
        s = data.get(k, {}).get("source")
        if s: return s
    return None

def api_thumb(title, size=600):
    q = urllib.parse.urlencode({"action":"query","format":"json","prop":"pageimages",
        "piprop":"thumbnail","pithumbsize":str(size),"titles":title,"redirects":"1"})
    data = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))
    for _, p in data.get("query", {}).get("pages", {}).items():
        s = p.get("thumbnail", {}).get("source")
        if s: return s
    return None

for key, titles in CANDIDATES.items():
    if manifest.get(key):
        continue
    got = False
    for title in titles:
        for fn in (rest_thumb, api_thumb):
            try:
                thumb = fn(title)
            except Exception as e:
                thumb = None
            if thumb:
                try:
                    raw = get(thumb)
                    ext = ".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                    with open(os.path.join(OUT, key + ext), "wb") as f:
                        f.write(raw)
                    manifest[key] = key + ext
                    print(f"OK      {key:10s} {len(raw):7d}  {title} via {fn.__name__}")
                    got = True
                    break
                except Exception as e:
                    print(f"  dlerr {key} {e}")
            time.sleep(2.5)
        if got: break
    if not got:
        print(f"FAIL    {key}")
    time.sleep(2.0)

json.dump(manifest, open(MAN, "w"), indent=2)
print("HAVE", sum(1 for v in manifest.values() if v), "images")
