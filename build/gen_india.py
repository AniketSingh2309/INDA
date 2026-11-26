# -*- coding: utf-8 -*-
import os, json, glob
from bgremove import to_data_uri

HERE = os.path.dirname(__file__)
GUNS = os.path.abspath(os.path.join(HERE, "..", "guns"))
CAND = os.path.join(GUNS, "cand")
FINAL = os.path.join(GUNS, "_final")
os.makedirs(FINAL, exist_ok=True)
OUTDIR = os.path.abspath(os.path.join(HERE, "..", "out"))
os.makedirs(OUTDIR, exist_ok=True)

import base64 as _b64
def _save_final(key, uri):
    if not uri: return
    try:
        b = _b64.b64decode(uri.split(",", 1)[1])
        open(os.path.join(FINAL, key + ".png"), "wb").write(b)
    except Exception:
        pass
manifest = json.load(open(os.path.join(GUNS, "_manifest.json")))

GOOD_LO, GOOD_HI = 0.05, 0.72  # accept a cutout whose foreground fraction lands in this band
TOL = {"rpg7": 5}              # per-image flood tolerance overrides (default 13)

def imgfile(key):
    fn = manifest.get(key)
    if fn and os.path.exists(os.path.join(GUNS, fn)):
        return os.path.join(GUNS, fn)
    return None

def candidate_files(key):
    return sorted(glob.glob(os.path.join(CAND, f"{key}__*.jpg")) + glob.glob(os.path.join(CAND, f"{key}__*.png")))

_pathcache = {}
def _cut_path(p, tol=13):
    k = (p, tol)
    if k not in _pathcache:
        _pathcache[k] = to_data_uri(p, tol=tol)
    return _pathcache[k]

def cutout(key, fallback=None, tol=13):
    sources = []
    mp = imgfile(key)
    if mp: sources.append((key, mp))
    for cp in candidate_files(key):
        sources.append((key + "-cand", cp))
    fb = imgfile(fallback) if fallback else None
    if fb: sources.append(("fb:" + fallback, fb))
    best_fb = None
    for tag, p in sources:
        uri, frac = _cut_path(p, tol)
        ok = uri and (GOOD_LO <= frac <= GOOD_HI)
        print(f"  cut {key:11s} via {tag:16s} frac={frac:.2f} {'ACCEPT' if ok else 'skip'}")
        if ok:
            _save_final(key, uri)
            return uri
        if uri and tag.startswith("fb:") and best_fb is None:
            best_fb = uri
    _save_final(key, best_fb)
    return best_fb

CATS = {
    "assault": ("Assault Rifles", "RFL"),
    "carbine": ("Carbines & SMGs", "CBN"),
    "sniper":  ("Sniper & Anti-Material", "SNP"),
    "lmg":     ("Machine Guns", "MG"),
    "pistol":  ("Sidearms / Pistols", "SDA"),
    "heavy":   ("Launchers & ATGM", "ATK"),
}

# key, name, cat, origin, svcYear, caliber, action, rof, range, weight, mag,
# ordered, arrived, assigned, madeIn, imgkey, imgfallback
W = [
 ("insas","INSAS Rifle 1B1","assault","India (OFB)","1998","5.56x45mm","Gas, rotating bolt","650 rpm","400 m","4.15 kg","20 rnd",420,420,372,True,"insas",None),
 ("excalibur","Excalibur Rifle","assault","India (OFB)","2015","5.56x45mm","Gas, short-stroke piston","600-650 rpm","400 m","3.8 kg","30 rnd",140,70,56,True,"excalibur","insas"),
 ("ak203","AK-203","assault","India / Russia (IRRPL, Amethi)","2023","7.62x39mm","Gas, long-stroke piston","600 rpm","500 m","3.8 kg","30 rnd",360,96,78,True,"ak203","akm"),
 ("sig716","SIG716i","assault","USA (imported)","2019","7.62x51mm NATO","Gas, short-stroke piston","685 rpm","600 m","4.3 kg","20 rnd",150,150,141,False,"sig716","m4"),
 ("tavor","IWI Tavor X95","assault","Israel","2010","5.56x45mm","Gas piston, bullpup","750-900 rpm","500 m","3.3 kg","30 rnd",96,96,88,False,"tavor",None),
 ("akm","AKM / Type 56","assault","USSR (legacy)","1965","7.62x39mm","Gas, long-stroke piston","600 rpm","350 m","3.1 kg","30 rnd",140,140,84,False,"akm",None),
 ("m4","Colt M4A1 (Para SF)","assault","USA","2005","5.56x45mm","Gas, direct impingement","700-950 rpm","500 m","3.4 kg","30 rnd",48,32,28,False,"m4",None),

 ("jvpc","JVPC Carbine","carbine","India (OFB)","2021","5.56x30mm MINSAS","Gas-operated","700 rpm","300 m","3.0 kg","30 rnd",180,84,66,True,"jvpc",None),
 ("msmc","Modern Sub-Machine Carbine","carbine","India (ARDE/OFB)","2013","5.56x30mm","Blowback","900 rpm","200 m","3.0 kg","30 rnd",90,0,0,True,"msmc",None),
 ("asmi","ASMI SMG","carbine","India (DRDO/AWEIL)","2021","9x19mm","Blowback","850 rpm","100 m","2.0 kg","33 rnd",120,44,33,True,"asmi","mp5"),
 ("mp5","Heckler & Koch MP5","carbine","Germany","1994","9x19mm","Roller-delayed blowback","800 rpm","200 m","2.5 kg","30 rnd",72,72,60,False,"mp5",None),

 ("svd","Dragunov SVD","sniper","USSR","1992","7.62x54mmR","Gas, semi-automatic","Semi-auto","800 m","4.3 kg","10 rnd",56,56,47,False,"svd",None),
 ("sako","SAKO TRG-42","sniper","Finland","2012","0.338 Lapua Magnum","Bolt-action","Bolt-action","1,500 m","5.1 kg","5 rnd",36,24,19,False,"sako","svd"),
 ("galil","IMI Galil Galatz","sniper","Israel","2003","7.62x51mm NATO","Gas, semi-automatic","Semi-auto","800 m","4.0 kg","25 rnd",28,28,21,False,"galil",None),
 ("vidhwansak","Vidhwansak AMR","sniper","India (OFB)","2007","12.7x108mm","Bolt-action","Bolt-action","1,800 m","25 kg","5 rnd",44,24,16,True,"vidhwansak",None),
 ("barrett","Barrett M95","sniper","USA (imported)","2018",".50 BMG (12.7x99mm)","Bolt-action bullpup","Bolt-action","1,800 m","10.0 kg","5 rnd",18,0,0,False,"m82",None),

 ("insaslmg","INSAS LMG","lmg","India (OFB)","1998","5.56x45mm","Gas, open bolt","600 rpm","700 m","6.2 kg","20 rnd",140,140,112,True,"insas",None),
 ("negev","IWI Negev NG7","lmg","Israel","2018","7.62x51mm NATO","Gas, open bolt","600-700 rpm","1,000 m","7.6 kg","belt-fed",66,40,31,False,"negev","pkm"),
 ("pkm","PKM","lmg","USSR","1990","7.62x54mmR","Gas, open bolt","650-750 rpm","1,000 m","7.5 kg","belt-fed",50,50,40,False,"pkm",None),

 ("auto9mm","Pistol Auto 9mm 1A","pistol","India (OFB)","1984","9x19mm","Short recoil (Hi-Power)","Semi-auto","50 m","1.0 kg","13 rnd",320,320,266,True,"auto9mm","glock"),
 ("glock","Glock 17 Gen4","pistol","Austria","2012","9x19mm","Short recoil, striker-fired","Semi-auto","50 m","0.63 kg","17 rnd",130,88,76,False,"glock",None),

 ("carlg","Carl Gustaf M4","heavy","Sweden (Make-in-India, MIL)","2020","84mm","Recoilless rifle","6 rds/min","500-1,000 m","6.6 kg","1 round",64,30,23,True,"carlg",None),
 ("rpg7","RPG-7 / variants","heavy","USSR","1985","40mm (PG-7 rocket)","Recoilless, reloadable","4-6 rds/min","200-500 m","6.3 kg","1 rocket",40,40,27,False,"rpg7",None),
 ("milan","MILAN ATGM","heavy","France (Make-in-India, BDL)","1982","115mm missile","Wire-guided ATGM","3-4 /min","2,000 m","7.1 kg","1 missile",44,0,0,True,"milan","rpg7"),
]

counters = {}
def make_codes(cat, n):
    pre = CATS[cat][1]
    val = counters.get(pre, 4100)
    out = []
    for _ in range(n):
        val += 7
        out.append(f"{pre}-{val:04d}")
    counters[pre] = val
    return out

weapons = []
for (key,name,cat,origin,year,cal,action,rof,rng,weight,mag,ordered,arrived,assigned,madeIn,ik,ifb) in W:
    assigned = min(assigned, arrived)
    remaining = ordered - arrived
    status = "production" if arrived==0 else ("deployed" if arrived>=ordered else "partial")
    weapons.append({
        "key":key,"name":name,"cat":cat,"catLabel":CATS[cat][0],"origin":origin,"year":year,
        "caliber":cal,"action":action,"rof":rof,"range":rng,"weight":weight,"mag":mag,
        "ordered":ordered,"arrived":arrived,"remaining":remaining,"assigned":assigned,
        "status":status,"madeIn":madeIn,"codes":make_codes(cat,assigned),
        "img":cutout(ik,ifb,TOL.get(ik,13)),
    })

payload = {"weapons":weapons,"catOrder":list(CATS.keys()),"catLabels":{k:v[0] for k,v in CATS.items()}}
DATA = json.dumps(payload, ensure_ascii=False)
tpl = open(os.path.join(HERE,"template.html"), encoding="utf-8").read()
html = tpl.replace("/*__DATA__*/null", DATA).replace("__ASOF__","24 NOV 2026")
open(os.path.join(OUTDIR,"index.html"),"w",encoding="utf-8").write(html)
print("wrote", round(os.path.getsize(os.path.join(OUTDIR,"index.html"))/1024/1024,2),"MB")
miss=[w["key"] for w in weapons if not w["img"]]
print("weapons",len(weapons),"with cutout",sum(1 for w in weapons if w["img"]),"missing",miss)
