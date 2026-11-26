import json, os, urllib.request, urllib.parse, time
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "guns"))
CAND = os.path.join(OUT, "cand"); os.makedirs(CAND, exist_ok=True)
UA="GameInventoryDashboard/1.0 (educational game project)"
BAD=("logo","icon",".svg","flag","commons","edit","ogg","symbol","map","diagram","disambig","users","barnstar","cartridge","round","ammunition","patch","insignia","emblem")

# key -> list of article titles to pull candidate images from
TARGETS = {
 "ak203":  ["AK-203","Kalashnikov AK-12","AK-12","Kalashnikov AK-200 series"],
 "sig716": ["SIG716","SIG516","SIG MCX"],
 "negev":  ["IWI Negev","IMI Negev"],
 "auto9mm":["Browning Hi-Power","Pistol Auto 9mm 1A"],
 "glock":  ["Glock 17","Glock 19","Glock 22","Glock"],
 "sako":   ["Sako TRG","SAKO TRG-42"],
 "milan":  ["MILAN","MILAN (missile)"],
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
    q=urllib.parse.urlencode({"action":"query","format":"json","generator":"images","gimlimit":"80","titles":title,"redirects":"1","prop":"imageinfo","iiprop":"url|mime|size","iiurlwidth":"640"})
    d=json.loads(get("https://en.wikipedia.org/w/api.php?"+q)); out=[]
    for _,p in d.get("query",{}).get("pages",{}).items():
        ii=(p.get("imageinfo") or [{}])[0]; mime=ii.get("mime",""); t=p.get("title","").lower()
        thumb=ii.get("thumburl") or ii.get("url"); wpx=ii.get("thumbwidth",0) or ii.get("width",0)
        if thumb and mime in ("image/jpeg","image/png") and not any(b in t for b in BAD):
            out.append((p.get("title",""),thumb))
    return out

for key,titles in TARGETS.items():
    got=0
    seen=set()
    for title in titles:
        try: cands=imglist(title)
        except Exception as e: print("listerr",key,title,e); cands=[]
        words=[w.lower() for w in title.replace("-"," ").split() if len(w)>2]
        cands.sort(key=lambda it:-sum(w in it[0].lower() for w in words))
        for name,thumb in cands:
            if got>=6: break
            if name in seen: continue
            seen.add(name)
            try:
                raw=get(thumb); ext=".png" if thumb.lower().split("?")[0].endswith(".png") else ".jpg"
                open(os.path.join(CAND,f"{key}__{got}{ext}"),"wb").write(raw)
                print(f"OK {key} #{got} {len(raw):7d} <- {name}"); got+=1
            except Exception as e: print("dlerr",key,e)
            time.sleep(1.8)
        if got>=6: break
        time.sleep(1.5)
    print(f"-- {key}: {got} candidates")
print("done")
