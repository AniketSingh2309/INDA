import json, os, urllib.request, urllib.parse, time

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
manifest = json.load(open(MAN)) if os.path.exists(MAN) else {}
UA = "GameInventoryDashboard/1.0 (educational game project)"

TARGETS = {
    "fal": "FN FAL",
    "cheytac": "CheyTac Intervention",
    "rem870": "Remington Model 870",
    "benelli": "Benelli M4",
}
BAD = ("logo","icon",".svg","flag","commons","edit","ogg","barnstar","symbol","map","diagram","disambig")

def get(url):
    for a in range(6):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=40) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(5*(a+1)); continue
            raise
    raise RuntimeError("429")

def list_images(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"40",
        "titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime","iiurlwidth":"520"})
    data=json.loads(get("https://en.wikipedia.org/w/api.php?"+q))
    pages=data.get("query",{}).get("pages",{})
    out=[]
    for _,p in pages.items():
        ii=p.get("imageinfo",[{}])[0]
        title_l=p.get("title","").lower()
        mime=ii.get("mime","")
        thumb=ii.get("thumburl") or ii.get("url")
        if not thumb: continue
        if mime not in ("image/jpeg","image/png"): continue
        if any(b in title_l for b in BAD): continue
        out.append((p.get("title",""),thumb))
    return out

for key,title in TARGETS.items():
    if manifest.get(key): continue
    try:
        imgs=list_images(title)
        if not imgs:
            print("NONE",key); continue
        # prefer an image whose filename shares a word with the weapon
        words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
        imgs.sort(key=lambda it: -sum(w in it[0].lower() for w in words))
        name,thumb=imgs[0]
        raw=get(thumb)
        ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
        open(os.path.join(OUT,key+ext),"wb").write(raw)
        manifest[key]=key+ext
        print(f"OK   {key:8s} {len(raw):7d}  <- {name}")
    except Exception as e:
        print("ERR",key,e)
    time.sleep(2.5)

json.dump(manifest,open(MAN,"w"),indent=2)
print("HAVE",sum(1 for v in manifest.values() if v))
