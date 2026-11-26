import json, os, urllib.request, urllib.parse, time
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
m = json.load(open(MAN)) if os.path.exists(MAN) else {}
UA="GameInventoryDashboard/1.0 (educational game project)"
BAD=("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","disambig","chart","cutaway")

# key -> candidate titles ; also distinct images for duplicated armor/plate
TARGETS = {
 "acog":            ["Trijicon ACOG","Advanced Combat Optical Gunsight","ACOG"],
 "magazine":        ["Magazine (firearms)","STANAG magazine"],
 "trench":          ["Trench knife","M3 fighting knife"],
 "smoke":           ["Smoke grenade","M18 smoke grenade"],
 "ballistichelmet": ["Modular Integrated Communications Helmet","Combat helmet","PASGT"],
 "pasgt":           ["PASGT","Personnel armor system for ground troops"],
 # distinct replacements (these shared one generic vest image)
 "platecarrier":    ["Plate carrier","Modular Tactical Vest"],
 "iotv":            ["Improved Outer Tactical Vest","Modular Scalable Vest"],
 "trauma":          ["Trauma plate","Ballistic vest"],
}
FORCE = {"platecarrier","iotv","trauma"}  # overwrite the duplicated image

def get(u):
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=50) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(8*(a+1)); continue
            raise
    raise RuntimeError("429")
def imglist(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"60","titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime","iiurlwidth":"640"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q)); out=[]
    for _,p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url")
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            out.append((p.get("title",""),thumb))
    return out
def rest(title):
    u="https://en.wikipedia.org/api/rest_v1/page/summary/"+urllib.parse.quote(title.replace(" ","_"))
    try: d=json.loads(get(u))
    except Exception: return None
    for k in ("originalimage","thumbnail"):
        s=d.get(k,{}).get("source")
        if s and not s.lower().endswith(".svg"): return s
    return None

def have(key):
    for e in (".jpg",".png",".jpeg"):
        if os.path.exists(os.path.join(OUT,key+e)): return True
    return False

for key,titles in TARGETS.items():
    if have(key) and key not in FORCE:
        print("skip",key); continue
    got=False
    for title in titles:
        thumb=rest(title)
        if not thumb:
            time.sleep(2)
            try:
                c=imglist(title); words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
                c.sort(key=lambda x:-sum(w in x[0].lower() for w in words))
                if c: thumb=c[0][1]
            except Exception: pass
        if thumb:
            try:
                raw=get(thumb); ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                for e2 in (".jpg",".png",".jpeg"):
                    pp=os.path.join(OUT,key+e2)
                    if e2!=ext and os.path.exists(pp): os.remove(pp)
                open(os.path.join(OUT,key+ext),"wb").write(raw); m[key]=key+ext
                try: print(f"OK  {key:16s} {len(raw):7d} <- {title}")
                except Exception: print(f"OK  {key:16s} {len(raw):7d}")
                got=True; break
            except Exception as e: print("dlerr",key,e)
        time.sleep(3)
    if not got: print("FAIL",key)
    time.sleep(2)
json.dump(m,open(MAN,"w"),indent=2); print("RETRYDONE")
