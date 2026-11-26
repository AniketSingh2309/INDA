import json, os, urllib.request, urllib.parse, time
from equip_items import ITEMS
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
manifest = json.load(open(MAN)) if os.path.exists(MAN) else {}
UA="GameInventoryDashboard/1.0 (educational game project)"
BAD=("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","disambig","barnstar","chart")

def have(key):
    for e in (".jpg",".png",".jpeg"):
        if os.path.exists(os.path.join(OUT,key+e)): return True
    return False
def get(u):
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=45) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(6*(a+1)); continue
            raise
    raise RuntimeError("429")
def rest(title):
    u="https://en.wikipedia.org/api/rest_v1/page/summary/"+urllib.parse.quote(title.replace(" ","_"))
    try: d=json.loads(get(u))
    except Exception: return None
    for k in ("originalimage","thumbnail"):
        s=d.get(k,{}).get("source")
        if s and not s.lower().endswith(".svg"): return s
    return None
def pageimg(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","prop":"pageimages","piprop":"thumbnail","pithumbsize":"640","titles":title,"redirects":"1"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q))
    for _,p in d.get("query",{}).get("pages",{}).items():
        s=p.get("thumbnail",{}).get("source")
        if s: return s
    return None
def imglist(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"50","titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime","iiurlwidth":"640"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q)); out=[]
    for _,p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url")
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            out.append((p.get("title",""),thumb))
    return out

todo=[it for it in ITEMS if it.get("titles") and not have(it["key"])]
print("to fetch:", len(todo))
for it in todo:
    key=it["key"]; got=False
    for title in it["titles"]:
        thumb=None
        for fn in (rest, pageimg):
            try: thumb=fn(title)
            except Exception: thumb=None
            if thumb: break
            time.sleep(1.6)
        if not thumb:
            try:
                c=imglist(title); words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
                c.sort(key=lambda x:-sum(w in x[0].lower() for w in words))
                if c: thumb=c[0][1]
            except Exception: pass
            time.sleep(1.6)
        if thumb:
            try:
                raw=get(thumb); ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                open(os.path.join(OUT,key+ext),"wb").write(raw); manifest[key]=key+ext
                try: print(f"OK   {key:16s} {len(raw):7d} <- {title}")
                except Exception: print(f"OK   {key:16s} {len(raw):7d}")
                got=True; break
            except Exception as e: print("dlerr",key,e)
        time.sleep(2.2)
    if not got: print(f"FAIL {key}")
    time.sleep(1.5)
json.dump(manifest,open(MAN,"w"),indent=2)
print("DONE")
