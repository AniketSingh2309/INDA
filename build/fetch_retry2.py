import json, os, urllib.request, urllib.parse, time
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
MAN = os.path.join(OUT, "_manifest.json")
m = json.load(open(MAN)); UA="GameInventoryDashboard/1.0 (educational game project)"
BAD=("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","disambig","users","barnstar")

# force=True -> overwrite existing (for glock: replace macro with full pistol)
TARGETS = {
    "sako":   (["Sako TRG","SAKO TRG-42","SAKO TRG"], False),
    "milan":  (["MILAN","MILAN (missile)","MILAN antitank missile"], False),
    "asmi":   (["ASMI (submachine gun)","ASMI submachine gun","ASMI"], False),
    "glock":  (["Glock 17","Glock 19","Glock"], True),
}
def get(u):
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=45) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(7*(a+1)); continue
            raise
    raise RuntimeError("429")
def imglist(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"60","titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime|size","iiurlwidth":"640"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q)); cands=[]
    for _,p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url")
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            cands.append((p.get("title",""),thumb))
    return cands
def rest(title):
    u="https://en.wikipedia.org/api/rest_v1/page/summary/"+urllib.parse.quote(title.replace(" ","_"))
    try: d=json.loads(get(u))
    except Exception: return None
    for k in ("originalimage","thumbnail"):
        s=d.get(k,{}).get("source")
        if s and not s.lower().endswith(".svg"): return s
    return None

for key,(titles,force) in TARGETS.items():
    if m.get(key) and not force:
        print("skip",key); continue
    got=False
    for title in titles:
        thumb=rest(title);
        if not thumb:
            time.sleep(2)
            try:
                c=imglist(title); words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
                c.sort(key=lambda it:-sum(w in it[0].lower() for w in words))
                if c: thumb=c[0][1]
            except Exception: pass
        if thumb:
            try:
                raw=get(thumb); ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                # clear other-ext file to avoid stale
                for e2 in (".jpg",".png"):
                    pp=os.path.join(OUT,key+e2)
                    if e2!=ext and os.path.exists(pp): os.remove(pp)
                open(os.path.join(OUT,key+ext),"wb").write(raw); m[key]=key+ext
                print(f"OK  {key:8s} {len(raw):7d} <- {title}"); got=True; break
            except Exception as e: print("dlerr",key,e)
        time.sleep(3)
    if not got: print("FAIL",key)
    time.sleep(2)
json.dump(m,open(MAN,"w"),indent=2); print("HAVE",sum(1 for v in m.values() if v))
