import json, os, urllib.request, urllib.parse, time

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
os.makedirs(OUT, exist_ok=True)
MAN = os.path.join(OUT, "_manifest.json")
manifest = {}
if os.path.exists(MAN):
    manifest = json.load(open(MAN))

# alternate / corrected titles for stubborn ones
TITLES = {
    "fal": "FN FAL",
    "awm": "Accuracy International AWM",
    "cheytac": "CheyTac M200 Intervention",
    "uzi": "Uzi", "p90": "FN P90", "mp7": "Heckler & Koch MP7",
    "m249": "M249 light machine gun", "pkm": "PK machine gun", "rpk": "RPK",
    "m240": "M240 machine gun", "rem870": "Remington Model 870",
    "benelli": "Benelli M4", "spas12": "Franchi SPAS-12", "glock": "Glock 17",
    "m9": "Beretta M9", "deagle": "Desert Eagle", "p226": "SIG Sauer P226",
    "m1911": "M1911 pistol", "rpg7": "RPG-7", "m72": "M72 LAW",
    "carlg": "Carl Gustaf recoilless rifle",
}
UA = "GameInventoryDashboard/1.0 (educational game project; contact none)"

def get(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 3 * (attempt + 1)
                print(f"   429, wait {wait}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("gave up (429)")

def rest_thumb(title):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    data = json.loads(get(url))
    for k in ("originalimage", "thumbnail"):
        src = data.get(k, {}).get("source")
        if src:
            return src
    return None

todo = [k for k, t in TITLES.items() if not manifest.get(k)]
print("TODO:", todo)
for key in todo:
    title = TITLES[key]
    try:
        thumb = rest_thumb(title)
        if not thumb:
            print(f"NO-IMG  {key:10s} {title}")
            continue
        raw = get(thumb)
        ext = ".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
        with open(os.path.join(OUT, key + ext), "wb") as f:
            f.write(raw)
        manifest[key] = key + ext
        print(f"OK      {key:10s} {len(raw):7d}  {key+ext}")
    except Exception as e:
        print(f"ERR     {key:10s} {e}")
    time.sleep(1.2)

json.dump(manifest, open(MAN, "w"), indent=2)
print("HAVE", sum(1 for v in manifest.values() if v), "images")
