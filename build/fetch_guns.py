import json, os, sys, urllib.request, urllib.parse, time

OUT = os.path.join(os.path.dirname(__file__), "..", "guns")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

# key -> Wikipedia article title
WEAPONS = {
    "ak47": "AK-47",
    "akm": "AKM",
    "m4": "M4 carbine",
    "m16": "M16 rifle",
    "hk416": "Heckler & Koch HK416",
    "scar": "FN SCAR",
    "aug": "Steyr AUG",
    "tavor": "IWI Tavor",
    "fal": "FN FAL",
    "g3": "Heckler & Koch G3",
    "m14": "M14 rifle",
    "svd": "SVD (rifle)",
    "m82": "Barrett M82",
    "awm": "Accuracy International Arctic Warfare",
    "cheytac": "CheyTac Intervention",
    "mp5": "Heckler & Koch MP5",
    "uzi": "Uzi",
    "p90": "FN P90",
    "mp7": "Heckler & Koch MP7",
    "m249": "M249 light machine gun",
    "pkm": "PK machine gun",
    "rpk": "RPK",
    "m240": "M240 machine gun",
    "rem870": "Remington Model 870",
    "benelli": "Benelli M4",
    "spas12": "Franchi SPAS-12",
    "glock": "Glock",
    "m9": "Beretta M9",
    "deagle": "Desert Eagle",
    "p226": "SIG Sauer P226",
    "m1911": "M1911 pistol",
    "rpg7": "RPG-7",
    "m72": "M72 LAW",
    "carlg": "Carl Gustaf recoilless rifle",
}

UA = "GameInventoryDashboard/1.0 (educational game project)"

def api_thumb(title, size=520):
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "pageimages",
        "piprop": "thumbnail", "pithumbsize": str(size),
        "titles": title, "redirects": "1",
    })
    url = "https://en.wikipedia.org/w/api.php?" + q
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pages = data.get("query", {}).get("pages", {})
    for _, p in pages.items():
        thumb = p.get("thumbnail", {}).get("source")
        if thumb:
            return thumb
    return None

results = {}
for key, title in WEAPONS.items():
    try:
        thumb = api_thumb(title)
        if not thumb:
            print(f"NO-IMG  {key:10s} {title}")
            results[key] = None
            continue
        req = urllib.request.Request(thumb, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        ext = ".jpg"
        if thumb.lower().endswith(".png"):
            ext = ".png"
        path = os.path.join(OUT, key + ext)
        with open(path, "wb") as f:
            f.write(raw)
        results[key] = os.path.basename(path)
        print(f"OK      {key:10s} {len(raw):7d}  {os.path.basename(path)}")
    except Exception as e:
        print(f"ERR     {key:10s} {e}")
        results[key] = None
    time.sleep(0.2)

with open(os.path.join(OUT, "_manifest.json"), "w") as f:
    json.dump(results, f, indent=2)
print("DONE", sum(1 for v in results.values() if v), "/", len(WEAPONS))
