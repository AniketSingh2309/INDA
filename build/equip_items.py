# -*- coding: utf-8 -*-
# Full Indian Armed Forces equipment catalog for the game armoury.
from photomap import PHOTO  # weapon key -> real photo relative path

# sidebar top-level equipment types (order matters)
TYPES = [
    ("weapons",     "Weapons"),
    ("ammunition",  "Ammunition"),
    ("nightvision", "Night Vision & Optics"),
    ("drones",      "Drones / UAV"),
    ("armoured",    "Armoured Vehicles"),
    ("artillery",   "Artillery"),
    ("attachments", "Attachments & Optics"),
    ("melee",       "Melee"),
    ("explosives",  "Explosives"),
    ("helmets",     "Helmets"),
    ("armor",       "Body Armor"),
    ("plates",      "Armor Plates"),
    ("comms",       "Communications"),
]
# custody policy per category (configurable here; read by gen_site.py and the page):
#   tracked = personal-issue, may hold individually tracked assets + custody records
#   bulk    = unit-issue / restricted stock, aggregate counts only, no soldier custody
#   sealed  = sealed restricted stock, authorised store custody only, never soldier-level
CATEGORY_POLICY = {
    "weapons": "tracked", "melee": "tracked", "helmets": "tracked", "armor": "tracked",
    "plates": "tracked", "nightvision": "tracked", "comms": "tracked",
    "ammunition": "bulk", "attachments": "bulk", "drones": "bulk", "armoured": "bulk", "artillery": "bulk",
    "explosives": "sealed",
}
# assignment eligibility (single source of truth, read by the page's Store.eligibility):
#   custody policy -> holder type -> how it may be held. "asset" = individually tracked asset custody,
#   "stock" = quantity allocation from unassigned stock (authorised, audited), None = never.
#   Sealed stock (explosives) may go to a TEAM only, as an authorised stock allocation; never to a soldier.
ASSIGNMENT_RULES = {
    "tracked": {"Soldier": "asset", "Team": "asset"},
    "bulk":    {"Soldier": None,    "Team": "stock"},
    "sealed":  {"Soldier": None,    "Team": "stock"},
}

# Destination classification (overrides ASSIGNMENT_RULES for the categories listed; others keep the
# policy-based rules above). "individual" = Individual Soldier only, "team" = Team only.
# How it is held still follows CATEGORY_POLICY: tracked -> asset custody, bulk/sealed -> team stock allocation.
ASSIGNMENT_CLASS = {
    # Individual Soldier only
    "weapons": "individual",      # 1. personal guns, rifles, pistols
    "helmets": "individual",      # 2. helmets, jackets, body armour
    "armor": "individual",        # 2.
    "plates": "individual",       # 2.
    "nightvision": "individual",  # 3. personal night-vision / optics
    # Team only
    "explosives": "team",         # 1. grenades, mines, explosives
    "ammunition": "team",         # 2. ammunition
    "comms": "team",              # 3. shared radios / communication equipment
    "armoured": "team",           # 4. vehicles / shared transport
    # 5. shared tools and support equipment: no matching catalogue category yet
}

# custody selection hierarchy: broad group -> sub-group -> catalogue lines, matched by (type, sub);
# sub None = every line of that type. gen_site.py asserts every catalogue line lands in exactly one
# sub-group. Restricted groups are browsable but never selectable (custody follows CATEGORY_POLICY).
GROUPS = [
    ("firearms", "Firearms", [
        ("Pistols / Sidearms",           [("weapons", "Sidearm")]),
        ("Assault Rifles",               [("weapons", "Assault Rifle")]),
        ("Sniper / Precision Rifles",    [("weapons", "Sniper / Anti-Material")]),
        ("Submachine Guns & Carbines",   [("weapons", "Carbine / SMG")]),
        ("Machine Guns",                 [("weapons", "Machine Gun")]),
        ("Launchers / ATGM",             [("weapons", "Launcher / ATGM")]),
    ]),
    ("protective", "Protective Equipment", [
        ("Helmets",                          [("helmets", None)]),
        ("Body Armour / Bulletproof Jackets", [("armor", None)]),
        ("Protective Plates",                [("plates", None)]),
    ]),
    ("optics", "Night Vision & Optical", [
        ("Night Vision Goggles",         [("nightvision", "Goggles / Monocular")]),
        ("Weapon Night Sights",          [("nightvision", "Weapon NV Sight")]),
        ("Thermal Imagers",              [("nightvision", "Thermal Sight")]),
        ("Weapon Optics & Attachments",  [("attachments", None)]),
    ]),
    ("comms", "Communication Equipment", [
        ("Radios",                       [("comms", None)]),
    ]),
    ("vehicles", "Vehicles, Artillery & UAV", [
        ("Armoured Vehicles",            [("armoured", None)]),
        ("Artillery",                    [("artillery", None)]),
        ("Drones / UAV",                 [("drones", None)]),
    ]),
    ("other", "Other Equipment", [
        ("Edged Weapons",                [("melee", None)]),
    ]),
    ("restricted", "Restricted Stock", [
        ("Ammunition",                   [("ammunition", None)]),
        ("Grenades",                     [("explosives", "Grenade")]),
        ("Mines & Charges",              [("explosives", "Mine / Charge")]),
    ]),
]

# subcategory display order within the inventory
SUBS = [
    "Assault Rifle", "Carbine / SMG", "Sniper / Anti-Material", "Machine Gun",
    "Sidearm", "Launcher / ATGM",
    "Rifle Cartridge", "Pistol / SMG Cartridge", "Sniper / AMR Cartridge", "Magazine & Belt",
    "Goggles / Monocular", "Weapon NV Sight", "Thermal Sight",
    "UAV / Recon", "Loitering Munition", "Nano / Quadcopter",
    "Main Battle Tank", "Light Tank", "Infantry Combat Vehicle", "Armoured Carrier",
    "Towed Howitzer", "Self-Propelled Gun", "Rocket Artillery", "Mortar",
    "Optic", "Muzzle / Barrel", "Grip / Support", "Aiming / Laser", "Feed Device",
    "Edged Weapon",
    "Grenade", "Mine / Charge",
    "Combat Helmet", "Light Helmet",
    "Soft Armor", "Plate Carrier",
    "Hard Plate",
    "Field Radio",
]

def item(key, name, type, sub, origin, year, madeIn, ordered, arrived, assigned, prefix, specs, titles=None, photo=None, **extra):
    d = dict(key=key, name=name, type=type, sub=sub, origin=origin, year=year, madeIn=madeIn,
             ordered=ordered, arrived=arrived, assigned=assigned, prefix=prefix,
             specs=[{"l": l, "v": v} for (l, v) in specs], titles=titles, photo=photo)
    d.update(extra)
    return d

def wspecs(cal, action, rof, rng, weight, mag):
    return [("Caliber", cal), ("Rate of Fire", rof), ("Action", action),
            ("Eff. Range", rng), ("Weight", weight), ("Feed", mag)]

ITEMS = []

# ---------------- WEAPONS (reuse existing photos) ----------------
W = [
 ("insas","INSAS Rifle 1B1","Assault Rifle","India (OFB)","1998",True,420,420,372,"RFL",("5.56x45mm","Gas, rotating bolt","650 rpm","400 m","4.15 kg","20 rnd")),
 ("excalibur","Excalibur Rifle","Assault Rifle","India (OFB)","2015",True,140,70,56,"RFL",("5.56x45mm","Gas piston","600-650 rpm","400 m","3.8 kg","30 rnd")),
 ("ak203","AK-203","Assault Rifle","India / Russia (Amethi)","2023",True,360,96,78,"RFL",("7.62x39mm","Gas, long-stroke","600 rpm","500 m","3.8 kg","30 rnd")),
 ("sig716","SIG716i","Assault Rifle","USA (imported)","2019",False,150,150,141,"RFL",("7.62x51mm NATO","Gas, short-stroke","685 rpm","600 m","4.3 kg","20 rnd")),
 ("tavor","IWI Tavor X95","Assault Rifle","Israel","2010",False,96,96,88,"RFL",("5.56x45mm","Gas, bullpup","750-900 rpm","500 m","3.3 kg","30 rnd")),
 ("akm","AKM / Type 56","Assault Rifle","USSR (legacy)","1965",False,140,140,84,"RFL",("7.62x39mm","Gas, long-stroke","600 rpm","350 m","3.1 kg","30 rnd")),
 ("m4","Colt M4A1 (Para SF)","Assault Rifle","USA","2005",False,48,32,28,"RFL",("5.56x45mm","Gas, direct impingement","700-950 rpm","500 m","3.4 kg","30 rnd")),
 ("jvpc","JVPC Carbine","Carbine / SMG","India (OFB)","2021",True,180,84,66,"CBN",("5.56x30mm","Gas-operated","700 rpm","300 m","3.0 kg","30 rnd")),
 ("msmc","Modern Sub-Machine Carbine","Carbine / SMG","India (ARDE)","2013",True,90,0,0,"CBN",("5.56x30mm","Blowback","900 rpm","200 m","3.0 kg","30 rnd")),
 ("asmi","ASMI SMG","Carbine / SMG","India (DRDO)","2021",True,120,44,33,"CBN",("9x19mm","Blowback","850 rpm","100 m","2.0 kg","33 rnd")),
 ("mp5","Heckler & Koch MP5","Carbine / SMG","Germany","1994",False,72,72,60,"CBN",("9x19mm","Roller-delayed blowback","800 rpm","200 m","2.5 kg","30 rnd")),
 ("svd","Dragunov SVD","Sniper / Anti-Material","USSR","1992",False,56,56,47,"SNP",("7.62x54mmR","Gas, semi-auto","Semi-auto","800 m","4.3 kg","10 rnd")),
 ("sako","SAKO TRG-42","Sniper / Anti-Material","Finland","2012",False,36,24,19,"SNP",("0.338 Lapua Mag","Bolt-action","Bolt-action","1,500 m","5.1 kg","5 rnd")),
 ("galil","IMI Galil Galatz","Sniper / Anti-Material","Israel","2003",False,28,28,21,"SNP",("7.62x51mm","Gas, semi-auto","Semi-auto","800 m","4.0 kg","25 rnd")),
 ("vidhwansak","Vidhwansak AMR","Sniper / Anti-Material","India (OFB)","2007",True,44,24,16,"SNP",("12.7x108mm","Bolt-action","Bolt-action","1,800 m","25 kg","5 rnd")),
 ("barrett","Barrett M95","Sniper / Anti-Material","USA (imported)","2018",False,18,0,0,"SNP",(".50 BMG","Bolt-action bullpup","Bolt-action","1,800 m","10.0 kg","5 rnd")),
 ("insaslmg","INSAS LMG","Machine Gun","India (OFB)","1998",True,140,140,112,"MG",("5.56x45mm","Gas, open bolt","600 rpm","700 m","6.2 kg","20 rnd")),
 ("negev","IWI Negev NG7","Machine Gun","Israel","2018",False,66,40,31,"MG",("7.62x51mm","Gas, open bolt","600-700 rpm","1,000 m","7.6 kg","belt-fed")),
 ("pkm","PKM","Machine Gun","USSR","1990",False,50,50,40,"MG",("7.62x54mmR","Gas, open bolt","650-750 rpm","1,000 m","7.5 kg","belt-fed")),
 ("auto9mm","Pistol Auto 9mm 1A","Sidearm","India (OFB)","1984",True,320,320,266,"SDA",("9x19mm","Short recoil (Hi-Power)","Semi-auto","50 m","1.0 kg","13 rnd")),
 ("glock","Glock 17 Gen4","Sidearm","Austria","2012",False,130,88,76,"SDA",("9x19mm","Short recoil, striker","Semi-auto","50 m","0.63 kg","17 rnd")),
 ("carlg","Carl Gustaf M4","Launcher / ATGM","Sweden (Make-in-India)","2020",True,64,30,23,"ATK",("84mm","Recoilless rifle","6 rds/min","500-1,000 m","6.6 kg","1 round")),
 ("rpg7","RPG-7 / variants","Launcher / ATGM","USSR","1985",False,40,40,27,"ATK",("40mm rocket","Recoilless","4-6 rds/min","200-500 m","6.3 kg","1 rocket")),
 ("milan","MILAN ATGM","Launcher / ATGM","France (Make-in-India)","1982",True,44,0,0,"ATK",("115mm missile","Wire-guided ATGM","3-4 /min","2,000 m","7.1 kg","1 missile")),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,ws) in W:
    ITEMS.append(item(k,n,"weapons",sub,origin,yr,mii,o,a,asg,pre, wspecs(*ws), photo=PHOTO.get(k)))

# ---------------- ATTACHMENTS & OPTICS (unit stock, no soldier codes) ----------------
A = [
 ("reddot","Reflex Red-Dot Sight","Optic","India / Israel","2016",True,500,500,470,
   [("Type","Reflex collimator"),("Magnification","1x unmagnified"),("Mount","Picatinny rail"),("Reticle","2 MOA dot"),("Weight","120 g"),("Fits","Rifles / carbines")],
   ["Red dot sight"]),
 ("holo","Holographic Sight","Optic","USA (imported)","2017",False,220,160,150,
   [("Type","Holographic"),("Magnification","1x"),("Mount","Picatinny rail"),("Reticle","65 MOA ring / 1 MOA"),("Weight","320 g"),("Battery","CR123 / AA")],
   ["Holographic weapon sight","EOTech"]),
 ("acog","4x Combat Optic","Optic","USA (imported)","2015",False,180,120,110,
   [("Type","Prismatic telescopic"),("Magnification","4x32"),("Mount","Picatinny rail"),("Reticle","BDC chevron"),("Weight","0.6 kg"),("Illumination","Fibre / tritium")],
   ["Advanced Combat Optical Gunsight"]),
 ("pso1","PSO-1 Telescopic Sight","Optic","USSR","1990",False,90,90,72,
   [("Type","Telescopic (sniper)"),("Magnification","4x24"),("Mount","Side rail (Warsaw)"),("Reticle","Rangefinding"),("Weight","0.6 kg"),("Fits","Dragunov SVD")],
   ["PSO-1"]),
 ("suppressor","Sound Suppressor","Muzzle / Barrel","India (DRDO)","2019",True,160,70,55,
   [("Type","Muzzle suppressor"),("Function","Flash / sound reduction"),("Mount","Threaded / QD"),("Material","Stainless / Inconel"),("Weight","0.4 kg"),("Fits","5.56 / 7.62 / 9mm")],
   ["Silencer (firearms)"]),
 ("bipod","Folding Bipod","Grip / Support","India","2014",True,300,300,250,
   [("Type","Folding bipod"),("Mount","Picatinny / sling stud"),("Leg height","150-230 mm"),("Material","Aluminium alloy"),("Weight","0.3 kg"),("Fits","Rifles / LMG")],
   ["Bipod"]),
 ("laser","IR Laser / Aiming Module","Aiming / Laser","USA (imported)","2018",False,140,90,80,
   [("Type","IR + visible laser"),("Mode","Aiming / illumination"),("Mount","Picatinny rail"),("Range","IR to 600 m"),("Weight","0.2 kg"),("Use","Night / NVG ops")],
   ["Laser sight","AN/PEQ-15"]),
]
for (k,n,sub,origin,yr,mii,o,a,iss,specs,titles) in A:
    ITEMS.append(item(k,n,"attachments",sub,origin,yr,mii,o,a,iss,None,specs,titles=titles))

# ---------------- MELEE (personal issue) ----------------
M = [
 ("kukri","Khukuri (Gorkha)","Edged Weapon","India / Nepal","Service",True,600,600,540,"MEL",
   [("Type","Curved combat knife"),("Blade","30 cm, high-carbon steel"),("Overall","41 cm"),("Weight","0.6 kg"),("Edge","Forward-curved"),("Role","Gorkha close combat")],
   ["Kukri"]),
 ("bayonet","Multi-Purpose Bayonet","Edged Weapon","India (OFB)","1998",True,900,780,700,"MEL",
   [("Type","Knife bayonet"),("Blade","17 cm steel"),("Mount","INSAS / AK lug"),("Overall","30 cm"),("Weight","0.4 kg"),("Extra","Wire-cutter")],
   ["Bayonet"]),
 ("combatknife","Combat Utility Knife","Edged Weapon","India","2010",True,700,500,440,"MEL",
   [("Type","Fixed-blade knife"),("Blade","18 cm steel"),("Material","Stainless steel"),("Overall","30 cm"),("Weight","0.35 kg"),("Role","Utility / combat")],
   ["Combat knife","Ka-Bar"]),
 ("machete","Machete / Dao","Edged Weapon","India","Service",True,400,400,300,"MEL",
   [("Type","Chopping blade"),("Blade","35 cm"),("Material","Carbon steel"),("Overall","48 cm"),("Weight","0.6 kg"),("Role","Jungle / clearing")],
   ["Machete"]),
 ("trench","Trench Knife","Edged Weapon","USA / legacy","Service",False,120,80,60,"MEL",
   [("Type","Knuckle fighting knife"),("Blade","16 cm dagger"),("Guard","Knuckle-duster"),("Overall","30 cm"),("Weight","0.5 kg"),("Role","CQB")],
   ["Trench knife"]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs,titles) in M:
    ITEMS.append(item(k,n,"melee",sub,origin,yr,mii,o,a,asg,pre,specs,titles=titles))

# ---------------- EXPLOSIVES (unit stock) ----------------
E = [
 ("fraggrenade","Fragmentation Grenade","Grenade","India (OFB MMHG)","2020",True,2000,1400,0,
   [("Type","Fragmentation"),("Filling","Composition B"),("Weight","400 g"),("Fuze","4-5 s delay"),("Lethal radius","15 m"),("Throw range","30-40 m")],
   ["M67 grenade","Hand grenade"]),
 ("smoke","Smoke Grenade","Grenade","India (OFB)","2005",True,1500,1500,0,
   [("Type","Screening smoke"),("Filling","HC / coloured"),("Weight","540 g"),("Burn time","60-90 s"),("Colours","Red/green/white"),("Throw range","30 m")],
   ["Smoke grenade"]),
 ("stun","Stun Grenade","Grenade","India","2012",True,800,500,0,
   [("Type","Flash-bang"),("Output","170+ dB / flash"),("Weight","200 g"),("Fuze","1.5 s"),("Effect","5 s disorientation"),("Role","CQB / hostage")],
   ["Stun grenade"]),
 ("claymore","Claymore Directional Mine","Mine / Charge","India (OFB)","2008",True,600,420,0,
   [("Type","Directional AP mine"),("Filling","C-4 + 700 steel balls"),("Weight","1.6 kg"),("Arc","60 deg fan"),("Lethal range","50 m"),("Trigger","Command / tripwire")],
   ["M18 Claymore"]),
 ("c4","C-4 Plastic Explosive","Mine / Charge","USA / India","Service",False,500,500,0,
   [("Type","Plastic demolition charge"),("Base","RDX (91%)"),("Weight","1.25 kg block"),("Detonation","8,040 m/s"),("Use","Breaching / demolition"),("Stability","Very stable")],
   ["C-4 (explosive)"]),
 ("atmine","Anti-Tank Mine","Mine / Charge","India (OFB)","1990",True,400,260,0,
   [("Type","Blast AT mine"),("Filling","TNT / RDX"),("Weight","7-9 kg"),("Trigger","Pressure (180 kg)"),("Effect","Track / hull kill"),("Role","Area denial")],
   ["Anti-tank mine","Land mine"]),
]
for (k,n,sub,origin,yr,mii,o,a,iss,specs,titles) in E:
    ITEMS.append(item(k,n,"explosives",sub,origin,yr,mii,o,a,iss,None,specs,titles=titles))

# ---------------- HELMETS (personal issue) ----------------
H = [
 ("ballistichelmet","Ballistic Combat Helmet","Combat Helmet","India (MKU/Kanpur)","2017",True,900,760,700,"HLM",
   [("Type","Full-cut ballistic"),("Protection","NIJ IIIA"),("Material","Aramid / UHMWPE"),("Weight","1.3 kg"),("Rails","ARC + NVG mount"),("Standard","Bulletproof")],
   ["Combat helmet"]),
 ("pasgt","PASGT Helmet","Combat Helmet","USA / legacy","1990",False,400,400,320,"HLM",
   [("Type","PASGT cut"),("Protection","NIJ IIIA"),("Material","Kevlar 29"),("Weight","1.5 kg"),("Suspension","Sling / pad"),("Role","Legacy infantry")],
   ["PASGT"]),
 ("ach","Advanced Combat Helmet","Combat Helmet","USA (imported)","2015",False,300,220,180,"HLM",
   [("Type","High-cut ACH"),("Protection","NIJ IIIA"),("Material","Aramid"),("Weight","1.4 kg"),("Rails","Accessory rails"),("Use","Special forces")],
   ["Advanced Combat Helmet"]),
 ("patka","Patka Helmet","Light Helmet","India","2001",True,500,500,420,"HLM",
   [("Type","Patrol / soft helmet"),("Protection","Fragmentation"),("Material","Aramid"),("Weight","1.0 kg"),("Coverage","Crown + nape flap"),("Role","CI / patrol")],
   ["Patka (helmet)","Patka"]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs,titles) in H:
    ITEMS.append(item(k,n,"helmets",sub,origin,yr,mii,o,a,asg,pre,specs,titles=titles))

# ---------------- BODY ARMOR (personal issue) ----------------
AR = [
 ("bulletproofvest","Bulletproof Jacket (MKU)","Soft Armor","India (MKU/SMPP)","2019",True,800,620,560,"ARM",
   [("Type","Modular bulletproof jacket"),("Protection","NIJ III (w/ plates)"),("Material","Aramid soft + hard plates"),("Weight","9.0 kg"),("Coverage","Front/back/side"),("Standard","BIS 17051")],
   ["Bulletproof vest"]),
 ("platecarrier","Modular Plate Carrier","Plate Carrier","India","2020",True,700,500,440,"ARM",
   [("Type","Plate carrier"),("Protection","Plate-dependent"),("Material","Cordura nylon"),("Weight","1.4 kg (carrier)"),("MOLLE","Full webbing"),("Plates","Front/back/side")],
   ["Plate carrier"]),
 ("interceptor","Interceptor Body Armor","Soft Armor","USA / legacy","2005",False,300,300,240,"ARM",
   [("Type","Outer tactical vest"),("Protection","NIJ IIIA + SAPI"),("Material","Kevlar + ceramic"),("Weight","7.4 kg"),("Coverage","Torso + throat/groin"),("Role","Legacy")],
   ["Interceptor body armor"]),
 ("iotv","Improved Outer Tactical Vest","Soft Armor","USA (imported)","2016",False,220,140,120,"ARM",
   [("Type","IOTV"),("Protection","NIJ IIIA + ESAPI"),("Material","Kevlar + ceramic"),("Weight","13 kg (full)"),("Release","Quick-release"),("Use","Special forces")],
   ["Improved Outer Tactical Vest"]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs,titles) in AR:
    ITEMS.append(item(k,n,"armor",sub,origin,yr,mii,o,a,asg,pre,specs,titles=titles))

# ---------------- ARMOR PLATES (personal issue) ----------------
P = [
 ("sapi","SAPI Ballistic Plate","Hard Plate","India (MKU)","2018",True,1600,1200,1050,"PLT",
   [("Type","Small-Arms Protective Insert"),("Protection","NIJ III"),("Material","UHMWPE / ceramic"),("Weight","1.9 kg"),("Size","25 x 30 cm"),("Cut","SAPI / shooter")],
   ["Small Arms Protective Insert"]),
 ("esapi","ESAPI Hard Plate (Lvl IV)","Hard Plate","India / USA","2019",True,900,600,520,"PLT",
   [("Type","Enhanced SAPI"),("Protection","NIJ IV (AP)"),("Material","Boron carbide"),("Weight","2.5 kg"),("Size","25 x 30 cm"),("Rating","Stops .30-06 AP")],
   ["Small Arms Protective Insert"]),
 ("trauma","Soft Trauma Plate","Hard Plate","India","2015",True,1200,1200,1000,"PLT",
   [("Type","Backing trauma plate"),("Protection","NIJ IIIA"),("Material","Aramid laminate"),("Weight","0.9 kg"),("Size","25 x 30 cm"),("Use","Blunt-trauma backing")],
   ["Trauma plate"]),
 ("boron","Boron-Carbide Plate","Hard Plate","India (DRDO/BHEL)","2021",True,700,380,300,"PLT",
   [("Type","Lightweight hard plate"),("Protection","NIJ IV"),("Material","Boron carbide ceramic"),("Weight","1.9 kg"),("Size","25 x 30 cm"),("Note","Indigenous 'Bhabha Kavach'")],
   ["Boron carbide"]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs,titles) in P:
    ITEMS.append(item(k,n,"plates",sub,origin,yr,mii,o,a,asg,pre,specs,titles=titles))

# ---------------- AMMUNITION (unit stock; box + bullet serial register) ----------------
def ammo(key, name, sub, origin, year, mii, o, a, iss, caliber, btype, vel, rpb, used, scode, imgkey):
    specs = [("Caliber", caliber), ("Bullet Type", btype), ("Muzzle Velocity", vel),
             ("Rounds / Box", f"{rpb}"), ("Used By", ", ".join(used)), ("Casing", "Brass / steel")]
    return item(key, name, "ammunition", sub, origin, year, mii, o, a, iss, None, specs,
                ammo=True, caliber=caliber, bulletType=btype, rpb=rpb, usedBy=used, scode=scode, imgkey=imgkey)

AMMO = [
 ammo("a556ball","5.56x45mm Ball (FMJ)","Rifle Cartridge","India (OFB Khadki)","2000",True,2400000,2100000,1780000,"5.56x45mm NATO","FMJ Ball (SS109)","920 m/s",900,["INSAS","Excalibur","M4A1","Tavor X95","INSAS LMG"],"556B","cal556"),
 ammo("a556tr","5.56x45mm Tracer","Rifle Cartridge","India (OFB)","2004",True,400000,300000,240000,"5.56x45mm NATO","Tracer (red trace)","900 m/s",900,["INSAS","Excalibur","Tavor X95"],"556T","cal556"),
 ammo("a556ap","5.56x45mm AP","Rifle Cartridge","USA (imported)","2015",False,200000,120000,90000,"5.56x45mm NATO","Armour-Piercing (M995)","930 m/s",900,["M4A1","Tavor X95"],"556A","cal556"),
 ammo("a762sb","7.62x39mm Ball","Rifle Cartridge","USSR / India","1965",False,1200000,1200000,980000,"7.62x39mm","FMJ Ball (M43)","730 m/s",700,["AK-203","AKM"],"762SB","cal762x39"),
 ammo("a762st","7.62x39mm Tracer","Rifle Cartridge","India (OFB)","2023",True,300000,200000,150000,"7.62x39mm","Tracer (T-45)","730 m/s",700,["AK-203","AKM"],"762ST","cal762x39"),
 ammo("a762lb","7.62x51mm Ball","Rifle Cartridge","India (OFB)","1990",True,800000,640000,520000,"7.62x51mm NATO","FMJ Ball (M80)","833 m/s",500,["SIG716i","Negev NG7","Galil"],"762LB","cal762x51"),
 ammo("a762lm","7.62x51mm Match (DMR)","Rifle Cartridge","India (OFB)","2019",True,120000,90000,60000,"7.62x51mm NATO","OTM Match","800 m/s",500,["SIG716i","Galil"],"762LM","cal762x51"),
 ammo("a762rb","7.62x54mmR Ball","Rifle Cartridge","USSR","1990",False,600000,600000,470000,"7.62x54mmR","FMJ Ball (LPS)","830 m/s",440,["Dragunov SVD","PKM"],"762RB","cal762x54"),
 ammo("a762rs","7.62x54mmR Sniper (7N1)","Rifle Cartridge","Russia (imported)","1998",False,90000,60000,42000,"7.62x54mmR","Sniper match (7N1)","830 m/s",200,["Dragunov SVD"],"762RS","cal762x54"),
 ammo("a9b","9x19mm Ball (FMJ)","Pistol / SMG Cartridge","India (OFB)","1984",True,1500000,1500000,1250000,"9x19mm Parabellum","FMJ Ball","390 m/s",1000,["MP5","ASMI","Pistol Auto 9mm 1A","Glock 17"],"9MB","cal9"),
 ammo("a9jhp","9x19mm JHP","Pistol / SMG Cartridge","Imported","2016",False,200000,140000,100000,"9x19mm Parabellum","Jacketed Hollow Point","370 m/s",1000,["Glock 17","Pistol Auto 9mm 1A"],"9MJ","cal9"),
 ammo("a9sub","9x19mm Subsonic","Pistol / SMG Cartridge","India","2012",True,120000,80000,55000,"9x19mm Parabellum","Subsonic (147 gr)","320 m/s",1000,["MP5"],"9MS","cal9"),
 ammo("a530","5.56x30mm MINSAS","Pistol / SMG Cartridge","India (ARDE/OFB)","2013",True,300000,160000,120000,"5.56x30mm MINSAS","Reduced-recoil Ball","650 m/s",800,["JVPC","MSMC"],"530B","cal556"),
 ammo("a338","0.338 Lapua Magnum Match","Sniper / AMR Cartridge","Finland / India","2012",False,60000,42000,30000,"0.338 Lapua Magnum","OTM Match (Scenar)","915 m/s",100,["SAKO TRG-42"],"338M","cal338"),
 ammo("a50","0.50 BMG API","Sniper / AMR Cartridge","USA / India","2018",False,40000,24000,16000,"0.50 BMG (12.7x99mm)","API (M8)","890 m/s",100,["Barrett M95"],"50AP","cal50"),
 ammo("a127","12.7x108mm API-T","Sniper / AMR Cartridge","India (OFB)","2007",True,50000,30000,20000,"12.7x108mm","API-Tracer","840 m/s",70,["Vidhwansak AMR"],"127AT","cal127"),
]
ITEMS.extend(AMMO)

# magazines & belts (unit stock, no serial register)
MB = [
 ("mag556","5.56mm 30-rd Magazine","India (OFB)","2000",True,60000,52000,44000,
   [("Type","Detachable box mag"),("Capacity","30 rnd"),("Caliber","5.56x45mm"),("Material","Polymer / steel"),("Weight","0.12 kg"),("Fits","INSAS / AR-pattern")],"magpic"),
 ("mag762","7.62mm 30-rd AK Magazine","India / Russia","2023",True,40000,20000,16000,
   [("Type","Curved box mag"),("Capacity","30 rnd"),("Caliber","7.62x39mm"),("Material","Steel / polymer"),("Weight","0.33 kg"),("Fits","AK-203 / AKM")],"magpic"),
 ("mag9","9mm 17-rd Pistol Magazine","India (OFB)","1984",True,50000,50000,42000,
   [("Type","Double-stack mag"),("Capacity","13-17 rnd"),("Caliber","9x19mm"),("Material","Steel / polymer"),("Weight","0.08 kg"),("Fits","Glock 17 / Auto 9mm")],"magpic"),
 ("belt762","7.62mm Linked Belt (MG)","India (OFB)","1990",True,30000,22000,17000,
   [("Type","Disintegrating link belt"),("Capacity","100-250 rnd"),("Caliber","7.62x51 / 54R"),("Link","M13 / metallic"),("Weight","varies"),("Fits","Negev NG7 / PKM")],"belt"),
]
for (k,n,origin,yr,mii,o,a,iss,specs,imgkey) in MB:
    ITEMS.append(item(k,n,"ammunition","Magazine & Belt",origin,yr,mii,o,a,iss,None,specs,imgkey=imgkey))

# ---------------- NIGHT VISION & OPTICS ----------------
NV = [
 ("nvg_bino","Passive Night Vision Goggle","Goggles / Monocular","India (BEL)","2016",True,2600,2000,1800,"NVD",
   [("Type","Image Intensifier Gen-II+"),("Detection","300 m"),("FOV","40°"),("Weight","0.5 kg"),("Power","2x AA"),("Mount","Helmet bracket")],["Night-vision device"]),
 ("nvg_wpn","Night Vision Weapon Sight","Weapon NV Sight","India (BEL)","2017",True,1500,1100,980,"NVD",
   [("Type","I² clip-on sight"),("Detection","400 m"),("Magnification","1x / 4x"),("Weight","0.9 kg"),("Mount","Picatinny"),("Fits","INSAS / AK / SIG")],["Night sight"]),
 ("tws","Thermal Weapon Sight","Weapon NV Sight","India (DRDO/BEL)","2019",True,1200,800,700,"NVD",
   [("Type","Uncooled LWIR thermal"),("Detection","1,500 m"),("Resolution","640×480"),("Weight","1.1 kg"),("Mount","Picatinny"),("Use","Day / night")],["Thermal weapon sight"]),
 ("hhti","Handheld Thermal Imager","Thermal Sight","India (BEL)","2017",True,900,600,480,None,
   [("Type","Uncooled thermal monocular"),("Detection","2 km"),("Resolution","640×480"),("Weight","1.5 kg"),("Power","Li-ion"),("Role","Surveillance")],["Thermal imaging camera"]),
 ("driver_ns","Driver Night Sight (AFV)","Thermal Sight","India (BEL)","2016",True,700,500,400,None,
   [("Type","Driver's night periscope"),("Detection","1 km"),("Tech","Image intensifier"),("Weight","2.0 kg"),("Fit","Tanks / ICV"),("Role","Night mobility")],["Night-vision device"]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs,titles) in NV:
    ITEMS.append(item(k,n,"nightvision",sub,origin,yr,mii,o,a,asg,pre,specs,titles=titles))

# ---------------- DRONES / UAV ----------------
DR = [
 ("heron","IAI Heron (MALE UAV)","UAV / Recon","Israel","2005",False,90,70,60,
   [("Class","MALE UAV"),("Endurance","52 h"),("Ceiling","10,000 m"),("Payload","EO/IR + SAR"),("Range","1,000 km"),("Role","ISR / strike-recce")],["IAI Heron"]),
 ("searcher","IAI Searcher Mk II","UAV / Recon","Israel","2002",False,110,110,92,
   [("Class","Tactical UAV"),("Endurance","18 h"),("Ceiling","7,000 m"),("Payload","EO/IR"),("Range","300 km"),("Role","Battlefield ISR")],["IAI Searcher"]),
 ("tapas","TAPAS-BH (Rustom-II)","UAV / Recon","India (DRDO)","2023",True,40,10,6,
   [("Class","MALE UAV (indigenous)"),("Endurance","24 h"),("Ceiling","9,000 m"),("Payload","EO/IR + SAR"),("Range","250 km"),("Status","Under induction")],["DRDO TAPAS BH-201","Rustom"]),
 ("nishant","Nishant UAV","UAV / Recon","India (DRDO)","2011",True,24,24,18,
   [("Class","Tactical UAV"),("Endurance","4.5 h"),("Launch","Catapult"),("Payload","EO/IR"),("Range","160 km"),("Role","Recon / arty-spotting")],["DRDO Nishant"]),
 ("nagastra","Nagastra-1 Loitering Munition","Loitering Munition","India","2024",True,480,120,90,
   [("Class","Kamikaze drone"),("Endurance","60 min"),("Warhead","1 kg"),("Range","30 km"),("Guidance","GPS + man-in-loop"),("Role","Precision strike")],["Loitering munition"]),
 ("blackhornet","Black Hornet Nano","Nano / Quadcopter","Norway","2022",False,600,400,340,
   [("Class","Nano UAV"),("Weight","33 g"),("Endurance","25 min"),("Range","2 km"),("Payload","EO/IR micro-cam"),("Role","Section recon")],["Black Hornet Nano"]),
 ("quad","Quadcopter Recon Drone","Nano / Quadcopter","India","2020",True,1400,1000,880,
   [("Class","Small quadcopter"),("Endurance","40 min"),("Range","7 km"),("Payload","4K + thermal"),("Weight","2.2 kg"),("Role","Patrol / surveillance")],["Quadcopter"]),
]
for (k,n,sub,origin,yr,mii,o,a,iss,specs,titles) in DR:
    ITEMS.append(item(k,n,"drones",sub,origin,yr,mii,o,a,iss,None,specs,titles=titles))

# ---------------- ARMOURED VEHICLES ----------------
AV = [
 ("t90","T-90S Bhishma (MBT)","Main Battle Tank","Russia / India","2003",True,1300,1100,1000,
   [("Main Gun","125 mm smoothbore"),("Weight","46 t"),("Crew","3"),("Engine","1,000 hp"),("Speed","60 km/h"),("Protection","ERA + composite")],["T-90"]),
 ("t72","T-72 Ajeya (MBT)","Main Battle Tank","USSR / India","1980",True,2400,2400,2200,
   [("Main Gun","125 mm smoothbore"),("Weight","41 t"),("Crew","3"),("Engine","780 hp"),("Speed","60 km/h"),("Protection","Composite + ERA")],["T-72"]),
 ("arjun","Arjun Mk-1A (MBT)","Main Battle Tank","India (DRDO)","2004",True,240,140,120,
   [("Main Gun","120 mm rifled"),("Weight","68 t"),("Crew","4"),("Engine","1,400 hp"),("Speed","67 km/h"),("Protection","Kanchan composite")],["Arjun (tank)"]),
 ("zorawar","Zorawar Light Tank","Light Tank","India (DRDO/L&T)","2024",True,350,40,24,
   [("Main Gun","105 mm"),("Weight","25 t"),("Crew","4"),("Role","High-altitude / Ladakh"),("Mobility","Air-transportable"),("Status","Under trials")],["Zorawar (tank)","Zorawar light tank"]),
 ("bmp2","BMP-2 Sarath (ICV)","Infantry Combat Vehicle","USSR / India","1987",True,1800,1800,1600,
   [("Armament","30 mm cannon + ATGM"),("Weight","14 t"),("Crew","3 + 7"),("Speed","65 km/h"),("Amphibious","Yes"),("Role","Mechanised infantry")],["BMP-2"]),
 ("whap","WhAP 8×8 (Armoured Carrier)","Armoured Carrier","India (Tata/DRDO)","2020",True,200,90,70,
   [("Type","Wheeled APC 8×8"),("Weight","24 t"),("Crew","2 + 10"),("Armament","30 mm RCWS"),("Amphibious","Yes"),("Protection","STANAG IV")],["WhAP"]),
 ("mpv","Mine-Protected Vehicle (MPV)","Armoured Carrier","India","2010",True,500,380,320,
   [("Type","MRAP"),("Weight","16 t"),("Crew","2 + 12"),("Protection","Blast-protected hull"),("Role","CI / convoy escort"),("Mobility","4×4 / 6×6")],["Mine-resistant ambush protected vehicle"]),
]
for (k,n,sub,origin,yr,mii,o,a,iss,specs,titles) in AV:
    ITEMS.append(item(k,n,"armoured",sub,origin,yr,mii,o,a,iss,None,specs,titles=titles))

# ---------------- ARTILLERY ----------------
AT = [
 ("dhanush","Dhanush 155 mm/45 Howitzer","Towed Howitzer","India (OFB)","2019",True,414,160,120,
   [("Calibre","155 mm / 45 cal"),("Range","38 km"),("Rate","6 rpm burst"),("Weight","13 t"),("Crew","6-8"),("Origin","Indigenous (Bofors-derived)")],["Dhanush (howitzer)"]),
 ("m777","M777 Ultralight Howitzer","Towed Howitzer","USA","2019",False,145,145,130,
   [("Calibre","155 mm / 39 cal"),("Range","30 km (40 km Excalibur)"),("Weight","4.2 t"),("Crew","7"),("Mobility","Heli-liftable"),("Role","Mountain artillery")],["M777 howitzer"]),
 ("bofors","Bofors FH77B 155 mm","Towed Howitzer","Sweden","1987",False,410,410,360,
   [("Calibre","155 mm / 39 cal"),("Range","30 km"),("Rate","6 rpm"),("Weight","11.5 t"),("Crew","6"),("Service","Kargil-proven")],["Bofors 155 mm Field Howitzer"]),
 ("k9","K9 Vajra-T SPG","Self-Propelled Gun","S. Korea / India","2018",True,100,100,90,
   [("Calibre","155 mm / 52 cal"),("Type","Tracked SPG"),("Range","40 km"),("Weight","47 t"),("Crew","5"),("Speed","67 km/h")],["K9 Thunder"]),
 ("pinaka","Pinaka MBRL","Rocket Artillery","India (DRDO)","1999",True,240,180,150,
   [("Type","Multi-barrel rocket"),("Calibre","214 mm × 12"),("Range","38-75 km"),("Salvo","44 s"),("Mobility","Tatra 8×8"),("Origin","Indigenous")],["Pinaka multi-barrel rocket launcher"]),
 ("smerch","BM-30 Smerch MBRL","Rocket Artillery","Russia","2007",False,60,60,50,
   [("Type","Heavy MBRL"),("Calibre","300 mm × 12"),("Range","90 km"),("Salvo","38 s"),("Weight","43 t"),("Role","Deep strike")],["BM-30 Smerch"]),
 ("mortar120","120 mm Mortar","Mortar","India (OFB)","1990",True,1200,1000,880,
   [("Calibre","120 mm"),("Range","6-9 km"),("Rate","15 rpm"),("Weight","0.5 t"),("Crew","5"),("Role","Infantry fire support")],["120 mm mortar","Mortar (weapon)"]),
]
for (k,n,sub,origin,yr,mii,o,a,iss,specs,titles) in AT:
    ITEMS.append(item(k,n,"artillery",sub,origin,yr,mii,o,a,iss,None,specs,titles=titles))

# ---------------- COMMUNICATIONS ----------------
CM = [
 ("sdr_manpack","Software Defined Radio (Manpack)","Field Radio","India (BEL)","2022",True,400,160,120,"COM",
   [("Band","VHF / UHF"),("Range","25 km"),("Waveform","Secure SDR"),("Weight","4.8 kg"),("Power","Li-ion"),("Role","Company net")]),
 ("vhf_handheld","VHF Handheld Radio","Field Radio","India","2018",True,900,700,610,"COM",
   [("Band","VHF 30-88 MHz"),("Range","8 km"),("Encryption","Yes"),("Weight","0.9 kg"),("Power","Li-ion"),("Role","Section net")]),
]
for (k,n,sub,origin,yr,mii,o,a,asg,pre,specs) in CM:
    ITEMS.append(item(k,n,"comms",sub,origin,yr,mii,o,a,asg,pre,specs))

if __name__ == "__main__":
    from collections import Counter
    c = Counter(i["type"] for i in ITEMS)
    print("total items:", len(ITEMS))
    for t, l in TYPES:
        print(f"  {t:12s} {c.get(t,0)}  ({l})")
    need = [i["key"] for i in ITEMS if not i.get("photo") and i.get("titles")]
    print("need photos fetched:", len(need))
