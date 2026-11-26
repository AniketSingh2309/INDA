import json, os, urllib.request, urllib.parse, time
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
CAND = os.path.join(OUT, "cand")
UA="GameInventoryDashboard/1.0 (educational game project)"
BAD=("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","users","round","warhead","grenade","diagram")
def get(u):
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=45) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(7*(a+1)); continue
            raise
    raise RuntimeError("429")
def imglist(title):
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"70","titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime","iiurlwidth":"640"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q)); out=[]
    for _,p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url")
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            out.append((p.get("title",""),thumb))
    return out
got=0; seen=set()
for title in ["RPG-7","RPG-7 variants"]:
    try: c=imglist(title)
    except Exception as e: c=[]; print("listerr",e)
    c.sort(key=lambda it:-sum(w in it[0].lower() for w in ("rpg","launcher","7v")))
    for name,thumb in c:
        if got>=6: break
        if name in seen: continue
        seen.add(name)
        try:
            raw=get(thumb); ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
            open(os.path.join(CAND,f"rpg7__{got}{ext}"),"wb").write(raw)
            try: print(f"OK rpg7 #{got} {len(raw):7d} <- {name}")
            except Exception: print(f"OK rpg7 #{got} {len(raw):7d}")
            got+=1
        except Exception as e: print("dlerr",e)
        time.sleep(1.8)
    if got>=6: break
    time.sleep(1.5)
print("rpg7 candidates:",got)
