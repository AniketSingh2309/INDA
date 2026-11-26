# -*- coding: utf-8 -*-
import os, json, base64, io
from PIL import Image

HERE = os.path.dirname(__file__)
GUNS = os.path.abspath(os.path.join(HERE, "..", "guns"))
OUTDIR = os.path.abspath(os.path.join(HERE, "..", "out"))
os.makedirs(OUTDIR, exist_ok=True)
manifest = json.load(open(os.path.join(GUNS, "_manifest.json")))

def data_uri(key):
    fn = manifest.get(key)
    if not fn:
        return None
    path = os.path.join(GUNS, fn)
    if not os.path.exists(path):
        return None
    try:
        im = Image.open(path)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (244, 244, 240))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((500, 500))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=74, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print("imgerr", key, e)
        return None

# category key -> (label, soldier-code prefix)
CATS = {
    "assault":  ("Assault Rifles", "RFL"),
    "battle":   ("Battle Rifles", "BTL"),
    "sniper":   ("Sniper Rifles", "SNP"),
    "smg":      ("Submachine Guns", "SMG"),
    "lmg":      ("Light Machine Guns", "LMG"),
    "shotgun":  ("Shotguns", "SHG"),
    "pistol":   ("Sidearms / Pistols", "SDA"),
    "heavy":    ("Launchers / Heavy", "HVY"),
}

# key, name, cat, origin, year, caliber, action, rof, range, weight, mag, ordered, arrived, assigned
W = [
 ("ak47","AK-47","assault","USSR",1949,"7.62x39mm","Gas, long-stroke piston","600 rpm","350 m","3.47 kg","30 rnd",240,240,210),
 ("akm","AKM","assault","USSR",1959,"7.62x39mm","Gas, long-stroke piston","600 rpm","350 m","3.1 kg","30 rnd",180,150,120),
 ("m4","M4A1 Carbine","assault","USA",1994,"5.56x45mm NATO","Gas, direct impingement","700-950 rpm","500 m","3.4 kg","30 rnd",200,200,185),
 ("m16","M16A4","assault","USA",1964,"5.56x45mm NATO","Gas, direct impingement","700-950 rpm","550 m","3.9 kg","30 rnd",160,100,90),
 ("hk416","HK416","assault","Germany",2004,"5.56x45mm NATO","Gas, short-stroke piston","700-900 rpm","500 m","3.5 kg","30 rnd",120,120,108),
 ("scar","FN SCAR-L","assault","Belgium",2009,"5.56x45mm NATO","Gas, short-stroke piston","550-650 rpm","300 m","3.5 kg","30 rnd",90,60,50),
 ("aug","Steyr AUG A3","assault","Austria",1978,"5.56x45mm NATO","Gas piston, bullpup","680-750 rpm","500 m","3.6 kg","30 rnd",80,0,0),
 ("tavor","IWI Tavor TAR-21","assault","Israel",2001,"5.56x45mm NATO","Gas piston, bullpup","750-900 rpm","550 m","3.27 kg","30 rnd",100,70,60),

 ("fal","FN FAL","battle","Belgium",1953,"7.62x51mm NATO","Gas, tilting breechblock","650-700 rpm","600 m","4.3 kg","20 rnd",60,60,44),
 ("g3","Heckler & Koch G3","battle","Germany",1958,"7.62x51mm NATO","Roller-delayed blowback","500-600 rpm","600 m","4.4 kg","20 rnd",70,40,30),
 ("m14","M14 EBR","battle","USA",1959,"7.62x51mm NATO","Gas, rotating bolt","700-750 rpm","460 m","5.1 kg","20 rnd",50,0,0),

 ("svd","Dragunov SVD","sniper","USSR",1963,"7.62x54mmR","Gas, semi-automatic","Semi-auto","800 m","4.3 kg","10 rnd",40,36,30),
 ("m82","Barrett M82A1","sniper","USA",1989,".50 BMG (12.7x99mm)","Recoil-operated, semi-auto","Semi-auto","1,800 m","14.0 kg","10 rnd",24,18,14),
 ("awm","AI Arctic Warfare Magnum","sniper","United Kingdom",1997,".338 Lapua Magnum","Bolt-action","Bolt-action","1,500 m","6.5 kg","5 rnd",20,20,16),
 ("cheytac","CheyTac M200 Intervention","sniper","USA",2001,".408 CheyTac","Bolt-action","Bolt-action","2,000 m","12.3 kg","7 rnd",12,0,0),

 ("mp5","Heckler & Koch MP5","smg","Germany",1966,"9x19mm Parabellum","Roller-delayed blowback","800 rpm","200 m","2.5 kg","30 rnd",110,110,95),
 ("uzi","IMI Uzi","smg","Israel",1950,"9x19mm Parabellum","Blowback, open bolt","600 rpm","200 m","3.5 kg","32 rnd",70,50,40),
 ("p90","FN P90","smg","Belgium",1990,"5.7x28mm","Blowback, bullpup","900 rpm","200 m","2.6 kg","50 rnd",60,30,24),
 ("mp7","Heckler & Koch MP7A1","smg","Germany",2001,"4.6x30mm","Gas, short-stroke piston","950 rpm","200 m","1.9 kg","40 rnd",80,0,0),

 ("m249","M249 SAW","lmg","Belgium / USA",1984,"5.56x45mm NATO","Gas, open bolt","750-1,000 rpm","800 m","7.5 kg","200 belt",60,48,40),
 ("pkm","PKM","lmg","USSR",1961,"7.62x54mmR","Gas, open bolt","650-750 rpm","1,000 m","7.5 kg","100-250 belt",45,45,36),
 ("rpk","RPK","lmg","USSR",1961,"7.62x39mm","Gas, long-stroke piston","600 rpm","800 m","4.8 kg","40 / 75 rnd",50,20,15),
 ("m240","M240B","lmg","Belgium / USA",1977,"7.62x51mm NATO","Gas, open bolt","650-950 rpm","800 m","12.5 kg","belt-fed",30,0,0),

 ("rem870","Remington 870","shotgun","USA",1950,"12 gauge","Pump-action","Pump","40 m","3.6 kg","4+1 shell",70,70,55),
 ("benelli","Benelli M4 Super 90","shotgun","Italy",1998,"12 gauge","Gas, semi-automatic","Semi-auto","50 m","3.8 kg","7+1 shell",50,35,28),
 ("spas12","Franchi SPAS-12","shotgun","Italy",1979,"12 gauge","Pump / semi-auto","Dual-mode","40 m","4.4 kg","8+1 shell",30,0,0),

 ("glock","Glock 17","pistol","Austria",1982,"9x19mm Parabellum","Short recoil, striker-fired","Semi-auto","50 m","0.63 kg","17 rnd",300,300,260),
 ("m9","Beretta M9","pistol","Italy",1985,"9x19mm Parabellum","Short recoil, DA/SA","Semi-auto","50 m","0.95 kg","15 rnd",200,160,140),
 ("deagle","IMI Desert Eagle","pistol","Israel / USA",1983,".50 Action Express","Gas, rotating bolt","Semi-auto","60 m","2.0 kg","7 rnd",40,25,18),
 ("p226","SIG Sauer P226","pistol","Germany / USA",1984,"9x19mm Parabellum","Short recoil, DA/SA","Semi-auto","50 m","0.96 kg","15 rnd",150,90,78),
 ("m1911","Colt M1911A1","pistol","USA",1911,".45 ACP","Short recoil, single-action","Semi-auto","50 m","1.1 kg","7 rnd",120,0,0),

 ("rpg7","RPG-7","heavy","USSR",1961,"40mm (PG-7VL rocket)","Recoilless, reloadable","4-6 rds/min","200 m (moving)","6.3 kg","1 rocket",36,30,24),
 ("m72","M72 LAW","heavy","USA",1963,"66mm rocket","Disposable launcher","Single-shot","200 m","2.5 kg","1 rocket",100,80,60),
 ("carlg","Carl Gustaf M4","heavy","Sweden",1948,"84mm","Recoilless rifle","6 rds/min","500-1,000 m","6.6 kg","1 round",24,0,0),
]

# deterministic soldier-code generator (role-prefixed)
counters = {}
def make_codes(cat, n):
    pre = CATS[cat][1]
    start = counters.get(pre, 4100)
    codes = []
    val = start
    for _ in range(n):
        val += 7  # spread the numbers so they look issued, not sequential
        codes.append(f"{pre}-{val:04d}")
    counters[pre] = val
    return codes

weapons = []
for (key,name,cat,origin,year,cal,action,rof,rng,weight,mag,ordered,arrived,assigned) in W:
    assigned = min(assigned, arrived)
    remaining = ordered - arrived
    if arrived == 0:
        status = "production"
    elif arrived >= ordered:
        status = "deployed"
    else:
        status = "partial"
    weapons.append({
        "key": key, "name": name, "cat": cat, "catLabel": CATS[cat][0],
        "origin": origin, "year": year, "caliber": cal, "action": action,
        "rof": rof, "range": rng, "weight": weight, "mag": mag,
        "ordered": ordered, "arrived": arrived, "remaining": remaining,
        "assigned": assigned, "status": status,
        "codes": make_codes(cat, assigned),
        "img": data_uri(key),
    })

cat_order = list(CATS.keys())
cat_labels = {k: v[0] for k, v in CATS.items()}

payload = {"weapons": weapons, "catOrder": cat_order, "catLabels": cat_labels}
DATA = json.dumps(payload, ensure_ascii=False)

tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
html = tpl.replace("/*__DATA__*/null", DATA).replace("__ASOF__", "24 NOV 2026")
out = os.path.join(OUTDIR, "index.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, round(os.path.getsize(out)/1024/1024, 2), "MB")
with_img = sum(1 for w in weapons if w["img"])
print("weapons", len(weapons), "with photo", with_img, "missing", len(weapons)-with_img)
print("missing imgs:", [w["key"] for w in weapons if not w["img"]])
