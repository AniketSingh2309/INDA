# -*- coding: utf-8 -*-
import os, json, io, base64
from PIL import Image
from photomap import photo_path

HERE = os.path.dirname(__file__)
OUTDIR = os.path.abspath(os.path.join(HERE, "..", "out"))
os.makedirs(OUTDIR, exist_ok=True)

def photo_uri(key, maxdim=660, q=82):
    p = photo_path(key)
    if not p:
        return None
    try:
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((maxdim, maxdim))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print("imgerr", key, e)
        return None

CATS = {
    "assault": ("Assault Rifles", "RFL"),
    "carbine": ("Carbines & SMGs", "CBN"),
    "sniper":  ("Sniper & Anti-Material", "SNP"),
    "lmg":     ("Machine Guns", "MG"),
    "pistol":  ("Sidearms / Pistols", "SDA"),
    "heavy":   ("Launchers & ATGM", "ATK"),
}
# key,name,cat,origin,svcYear,caliber,action,rof,range,weight,mag,ordered,arrived,assigned,madeIn,imgkey
W = [
 ("insas","INSAS Rifle 1B1","assault","India (OFB)","1998","5.56x45mm","Gas, rotating bolt","650 rpm","400 m","4.15 kg","20 rnd",420,420,372,True,"insas"),
 ("excalibur","Excalibur Rifle","assault","India (OFB)","2015","5.56x45mm","Gas, short-stroke piston","600-650 rpm","400 m","3.8 kg","30 rnd",140,70,56,True,"excalibur"),
 ("ak203","AK-203","assault","India / Russia (IRRPL, Amethi)","2023","7.62x39mm","Gas, long-stroke piston","600 rpm","500 m","3.8 kg","30 rnd",360,96,78,True,"ak203"),
 ("sig716","SIG716i","assault","USA (imported)","2019","7.62x51mm NATO","Gas, short-stroke piston","685 rpm","600 m","4.3 kg","20 rnd",150,150,141,False,"sig716"),
 ("tavor","IWI Tavor X95","assault","Israel","2010","5.56x45mm","Gas piston, bullpup","750-900 rpm","500 m","3.3 kg","30 rnd",96,96,88,False,"tavor"),
 ("akm","AKM / Type 56","assault","USSR (legacy)","1965","7.62x39mm","Gas, long-stroke piston","600 rpm","350 m","3.1 kg","30 rnd",140,140,84,False,"akm"),
 ("m4","Colt M4A1 (Para SF)","assault","USA","2005","5.56x45mm","Gas, direct impingement","700-950 rpm","500 m","3.4 kg","30 rnd",48,32,28,False,"m4"),

 ("jvpc","JVPC Carbine","carbine","India (OFB)","2021","5.56x30mm MINSAS","Gas-operated","700 rpm","300 m","3.0 kg","30 rnd",180,84,66,True,"jvpc"),
 ("msmc","Modern Sub-Machine Carbine","carbine","India (ARDE/OFB)","2013","5.56x30mm","Blowback","900 rpm","200 m","3.0 kg","30 rnd",90,0,0,True,"msmc"),
 ("asmi","ASMI SMG","carbine","India (DRDO/AWEIL)","2021","9x19mm","Blowback","850 rpm","100 m","2.0 kg","33 rnd",120,44,33,True,"asmi"),
 ("mp5","Heckler & Koch MP5","carbine","Germany","1994","9x19mm","Roller-delayed blowback","800 rpm","200 m","2.5 kg","30 rnd",72,72,60,False,"mp5"),

 ("svd","Dragunov SVD","sniper","USSR","1992","7.62x54mmR","Gas, semi-automatic","Semi-auto","800 m","4.3 kg","10 rnd",56,56,47,False,"svd"),
 ("sako","SAKO TRG-42","sniper","Finland","2012","0.338 Lapua Magnum","Bolt-action","Bolt-action","1,500 m","5.1 kg","5 rnd",36,24,19,False,"sako"),
 ("galil","IMI Galil Galatz","sniper","Israel","2003","7.62x51mm NATO","Gas, semi-automatic","Semi-auto","800 m","4.0 kg","25 rnd",28,28,21,False,"galil"),
 ("vidhwansak","Vidhwansak AMR","sniper","India (OFB)","2007","12.7x108mm","Bolt-action","Bolt-action","1,800 m","25 kg","5 rnd",44,24,16,True,"vidhwansak"),
 ("barrett","Barrett M95","sniper","USA (imported)","2018",".50 BMG (12.7x99mm)","Bolt-action bullpup","Bolt-action","1,800 m","10.0 kg","5 rnd",18,0,0,False,"m82"),

 ("insaslmg","INSAS LMG","lmg","India (OFB)","1998","5.56x45mm","Gas, open bolt","600 rpm","700 m","6.2 kg","20 rnd",140,140,112,True,"insas"),
 ("negev","IWI Negev NG7","lmg","Israel","2018","7.62x51mm NATO","Gas, open bolt","600-700 rpm","1,000 m","7.6 kg","belt-fed",66,40,31,False,"negev"),
 ("pkm","PKM","lmg","USSR","1990","7.62x54mmR","Gas, open bolt","650-750 rpm","1,000 m","7.5 kg","belt-fed",50,50,40,False,"pkm"),

 ("auto9mm","Pistol Auto 9mm 1A","pistol","India (OFB)","1984","9x19mm","Short recoil (Hi-Power)","Semi-auto","50 m","1.0 kg","13 rnd",320,320,266,True,"auto9mm"),
 ("glock","Glock 17 Gen4","pistol","Austria","2012","9x19mm","Short recoil, striker-fired","Semi-auto","50 m","0.63 kg","17 rnd",130,88,76,False,"glock"),

 ("carlg","Carl Gustaf M4","heavy","Sweden (Make-in-India, MIL)","2020","84mm","Recoilless rifle","6 rds/min","500-1,000 m","6.6 kg","1 round",64,30,23,True,"carlg"),
 ("rpg7","RPG-7 / variants","heavy","USSR","1985","40mm (PG-7 rocket)","Recoilless, reloadable","4-6 rds/min","200-500 m","6.3 kg","1 rocket",40,40,27,False,"rpg7"),
 ("milan","MILAN ATGM","heavy","France (Make-in-India, BDL)","1982","115mm missile","Wire-guided ATGM","3-4 /min","2,000 m","7.1 kg","1 missile",44,0,0,True,"milan"),
]

counters = {}
def make_codes(cat, n):
    pre = CATS[cat][1]; val = counters.get(pre, 4100); out = []
    for _ in range(n):
        val += 7; out.append(f"{pre}-{val:04d}")
    counters[pre] = val; return out

_imgcache = {}
def img_for(ik):
    if ik not in _imgcache:
        _imgcache[ik] = photo_uri(ik)
        print(f"  photo {ik:11s} {'OK' if _imgcache[ik] else 'MISSING'}")
    return _imgcache[ik]

weapons = []
for (key,name,cat,origin,year,cal,action,rof,rng,weight,mag,ordered,arrived,assigned,madeIn,ik) in W:
    assigned = min(assigned, arrived); remaining = ordered - arrived
    status = "production" if arrived==0 else ("deployed" if arrived>=ordered else "partial")
    weapons.append({
        "key":key,"name":name,"cat":cat,"catLabel":CATS[cat][0],"origin":origin,"year":year,
        "caliber":cal,"action":action,"rof":rof,"range":rng,"weight":weight,"mag":mag,
        "ordered":ordered,"arrived":arrived,"remaining":remaining,"assigned":assigned,
        "status":status,"madeIn":madeIn,"codes":make_codes(cat,assigned),"img":img_for(ik),
    })

payload = {"weapons":weapons,"catOrder":list(CATS.keys()),"catLabels":{k:v[0] for k,v in CATS.items()}}
DATA = json.dumps(payload, ensure_ascii=False)
tpl = open(os.path.join(HERE,"template_photo.html"), encoding="utf-8").read()
html = tpl.replace("/*__DATA__*/null", DATA).replace("__ASOF__","24 NOV 2026")
open(os.path.join(OUTDIR,"index.html"),"w",encoding="utf-8").write(html)
print("wrote", round(os.path.getsize(os.path.join(OUTDIR,"index.html"))/1024/1024,2),"MB")
print("weapons",len(weapons),"with photo",sum(1 for w in weapons if w["img"]),"missing",[w["key"] for w in weapons if not w["img"]])
