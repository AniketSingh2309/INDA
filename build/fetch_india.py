import json, os, urllib.request, urllib.parse, time

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
manifest = json.load(open(MAN)) if os.path.exists(MAN) else {}
UA = "GameInventoryDashboard/1.0 (educational game project)"
BAD = ("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","disambig","barnstar","question")

# key -> candidate Wikipedia titles (first with an image wins)
TARGETS = {
    "insas":      ["INSAS", "INSAS rifle"],
    "ak203":      ["AK-203", "Kalashnikov AK-200 series", "AK-12"],
    "sig716":     ["SIG716", "SIG MCX SPEAR", "SIG516"],
    "jvpc":       ["Joint Venture Protective Carbine", "JVPC"],
    "msmc":       ["Modern Sub Machine Carbine", "MSMC"],
    "asmi":       ["ASMI (submachine gun)", "ASMI submachine gun"],
    "vidhwansak": ["Vidhwansak", "Vidhwansak multi-caliber anti-materiel rifle"],
    "sako":       ["Sako TRG", "SAKO TRG"],
    "galil":      ["IMI Galil", "Galil (rifle)"],
    "negev":      ["IWI Negev", "IMI Negev"],
    "auto9mm":    ["Pistol Auto 9mm 1A", "Browning Hi-Power"],
    "milan":      ["MILAN", "MILAN (missile)"],
    "excalibur":  ["Excalibur (rifle)", "INSAS"],
}

def get(url):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(6 * (a + 1)); continue
            raise
    raise RuntimeError("429")

def rest_thumb(title):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    try: d = json.loads(get(url))
    except Exception: return None
    for k in ("originalimage", "thumbnail"):
        s = d.get(k, {}).get("source")
        if s and not s.lower().endswith(".svg"): return s
    return None

def pageimg(title):
    q = urllib.parse.urlencode({"action":"query","format":"json","prop":"pageimages",
        "piprop":"thumbnail","pithumbsize":"640","titles":title,"redirects":"1"})
    d = json.loads(get("https://en.wikipedia.org/w/api.php?"+q))
    for _, p in d.get("query",{}).get("pages",{}).items():
        s = p.get("thumbnail",{}).get("source")
        if s: return s
    return None

def imglist(title):
    q = urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"50",
        "titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime","iiurlwidth":"640"})
    d = json.loads(get("https://en.wikipedia.org/w/api.php?"+q))
    cands=[]
    for _, p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url")
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            cands.append((p.get("title",""),thumb))
    return cands

for key, titles in TARGETS.items():
    if manifest.get(key):
        print("skip", key); continue
    got=False
    for title in titles:
        thumb=None
        for fn in (rest_thumb, pageimg):
            try: thumb=fn(title)
            except Exception: thumb=None
            if thumb: break
            time.sleep(2.0)
        if not thumb:
            try:
                cands=imglist(title)
                words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
                cands.sort(key=lambda it:-sum(w in it[0].lower() for w in words))
                if cands: thumb=cands[0][1]
            except Exception: pass
            time.sleep(2.0)
        if thumb:
            try:
                raw=get(thumb)
                ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                open(os.path.join(OUT,key+ext),"wb").write(raw)
                manifest[key]=key+ext
                print(f"OK   {key:11s} {len(raw):7d}  <- {title}")
                got=True; break
            except Exception as e:
                print("  dlerr",key,e)
        time.sleep(2.5)
    if not got: print(f"FAIL {key}")
    time.sleep(2.0)

json.dump(manifest, open(MAN,"w"), indent=2)
print("HAVE", sum(1 for v in manifest.values() if v))
