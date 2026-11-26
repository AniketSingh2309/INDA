# -*- coding: utf-8 -*-
import os, json, io, base64
from PIL import Image
from equip_items import ITEMS, TYPES, SUBS, CATEGORY_POLICY, GROUPS
from custody_seed import build_seed
from photomap import PHOTO

HERE = os.path.dirname(__file__)
GUNS = os.path.abspath(os.path.join(HERE, "..", "guns"))
OUTDIR = os.path.abspath(os.path.join(HERE, "..", "out"))
os.makedirs(OUTDIR, exist_ok=True)
TYPE_LABEL = dict(TYPES)

# reuse a same-class photo when an item's own image could not be fetched
FALLBACK = {
    "barrett": "m82", "insaslmg": "insas",
    "acog": "pso1", "magazine": "reddot", "trench": "combatknife",
    "smoke": "fraggrenade", "ballistichelmet": "ach", "pasgt": "ach", "boron": "sapi",
    # new categories — reuse a same-class photo that downloaded if the exact one didn't
    "nvg_wpn": "nvg_bino", "driver_ns": "hhti", "tws": "hhti",
    "heron": "quad", "searcher": "quad", "tapas": "quad", "nishant": "quad", "blackhornet": "quad",
    "t72": "t90", "bmp2": "whap", "mpv": "whap", "arjun": "t90", "zorawar": "t90",
    "dhanush": "m777", "bofors": "m777", "pinaka": "k9", "smerch": "k9", "mortar120": "m777",
}

def file_for_key(key):
    rel = PHOTO.get(key)
    if rel:
        p = os.path.join(GUNS, rel)
        if os.path.exists(p):
            return p
    for e in (".jpg", ".png", ".jpeg"):
        p = os.path.join(GUNS, key + e)
        if os.path.exists(p):
            return p
    return None

def resolve_photo(it):
    if it.get("photo"):
        p = os.path.join(GUNS, it["photo"])
        if os.path.exists(p):
            return p
    if it.get("imgkey"):
        p = file_for_key(it["imgkey"])
        if p:
            return p
    p = file_for_key(it["key"])
    if p:
        return p
    fb = FALLBACK.get(it["key"])
    if fb:
        q = file_for_key(fb)
        if q:
            return q
    if it.get("ammo"):
        return file_for_key("ammobox") or file_for_key("magpic")
    return None

_cache = {}
def photo_uri(it, maxdim=620, q=80):
    p = resolve_photo(it)
    if not p:
        return None
    if p in _cache:
        return _cache[p]
    try:
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1]); im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((maxdim, maxdim))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print("imgerr", it["key"], e); uri = None
    _cache[p] = uri
    return uri

counters = {}
def make_codes(prefix, n):
    val = counters.get(prefix, 4100); out = []
    for _ in range(n):
        val += 7; out.append(f"{prefix}-{val:04d}")
    counters[prefix] = val
    return out

import hashlib, datetime, math
TODAY = datetime.date(2026, 11, 24)
DEPOTS = ["COD Jabalpur", "AOC Centre Agra", "CAD Pulgaon", "OEF Hazratpur",
          "32 FAD Delhi Cantt", "COD Dehu Road", "AD Panagarh", "COD Chheoki"]
def _h(key, salt=""):
    return int(hashlib.md5((key + salt).encode()).hexdigest(), 16)
def fmt(d):
    return d.strftime("%d %b %Y")
def procurement(it, status):
    h = _h(it["key"])
    order = datetime.date(2025, 1, 1) + datetime.timedelta(days=h % 430)
    lead = datetime.timedelta(weeks=6 + (h // 13) % 26)
    depot = DEPOTS[h % len(DEPOTS)]
    batch = f"LOT-{it['year'] if str(it['year']).isdigit() else '24'}-{(h % 8999) + 1000}"
    if status == "production":
        exp = TODAY + datetime.timedelta(weeks=4 + (h % 22))
        delivery = "Expected " + fmt(exp)
    else:
        dd = order + lead
        if dd > TODAY:
            dd = TODAY - datetime.timedelta(days=h % 40)
        delivery = fmt(dd)
    return fmt(order), delivery, batch, depot

def ammo_register(it):
    rpb = it["rpb"]; arrived = it["arrived"]; ordered = it["ordered"]
    sc = it["scode"]
    boxes_in = max(1, math.ceil(arrived / rpb)) if arrived else 0
    boxes_pending = math.ceil((ordered - arrived) / rpb) if ordered > arrived else 0
    sample = []
    for i in range(1, min(boxes_in, 30) + 1):
        frm = (i - 1) * rpb + 1
        to = min(i * rpb, arrived)
        sample.append({"box": f"{sc}-BX-{i:05d}", "from": f"{sc}-{frm:07d}", "to": f"{sc}-{to:07d}", "rounds": to - frm + 1})
    return {
        "rpb": rpb, "boxesIn": boxes_in, "boxesPending": boxes_pending,
        "boxFrom": f"{sc}-BX-00001", "boxTo": f"{sc}-BX-{boxes_in:05d}" if boxes_in else "—",
        "bulletFrom": f"{sc}-0000001", "bulletTo": f"{sc}-{arrived:07d}" if arrived else "—",
        "sample": sample,
    }

out_items = []
missing = []
for it in ITEMS:
    assigned = min(it["assigned"], it["arrived"])
    remaining = it["ordered"] - it["arrived"]
    status = "production" if it["arrived"] == 0 else ("deployed" if it["arrived"] >= it["ordered"] else "partial")
    stock = it["prefix"] is None
    codes = [] if stock else make_codes(it["prefix"], assigned)
    img = photo_uri(it)
    if not img:
        missing.append(it["key"])
    orderDate, deliveryDate, batch, depot = procurement(it, status)
    if it["arrived"] > 0:
        reserve = (it["arrived"] - assigned) / it["arrived"]
        alert = "critical" if reserve <= 0.05 else ("low" if reserve <= 0.15 else "")
    else:
        alert = ""
    reorder = bool(alert) or status == "production"
    rec = {
        "key": it["key"], "name": it["name"], "type": it["type"], "typeLabel": TYPE_LABEL[it["type"]],
        "sub": it["sub"], "origin": it["origin"], "year": it["year"], "madeIn": it["madeIn"],
        "ordered": it["ordered"], "arrived": it["arrived"], "remaining": remaining, "assigned": assigned,
        "status": status, "stock": stock, "codes": codes, "specs": it["specs"], "img": img,
        "orderDate": orderDate, "deliveryDate": deliveryDate, "batch": batch, "depot": depot,
        "unit": "rounds" if it.get("ammo") else "units",
        "alert": alert, "reorder": reorder,
    }
    if it.get("ammo"):
        rec["ammo"] = True
        rec["caliber"] = it["caliber"]; rec["bulletType"] = it["bulletType"]
        rec["usedBy"] = it["usedBy"]; rec["reg"] = ammo_register(it)
    out_items.append(rec)

# weapon <-> ammunition cross-links by canonical caliber
WEAPON_CAL = {
 "insas":"556","excalibur":"556","m4":"556","tavor":"556","insaslmg":"556",
 "ak203":"762x39","akm":"762x39",
 "sig716":"762x51","negev":"762x51","galil":"762x51",
 "svd":"762x54","pkm":"762x54",
 "mp5":"9","asmi":"9","auto9mm":"9","glock":"9",
 "jvpc":"556x30","msmc":"556x30",
 "sako":"338","barrett":"50","vidhwansak":"127",
}
AMMO_CAL = {
 "a556ball":"556","a556tr":"556","a556ap":"556",
 "a762sb":"762x39","a762st":"762x39",
 "a762lb":"762x51","a762lm":"762x51",
 "a762rb":"762x54","a762rs":"762x54",
 "a9b":"9","a9jhp":"9","a9sub":"9",
 "a530":"556x30","a338":"338","a50":"50","a127":"127",
}
cal_w, cal_a = {}, {}
for r in out_items:
    if r["key"] in WEAPON_CAL: cal_w.setdefault(WEAPON_CAL[r["key"]], []).append(r)
    if r["key"] in AMMO_CAL:   cal_a.setdefault(AMMO_CAL[r["key"]], []).append(r)
for r in out_items:
    if r["key"] in WEAPON_CAL:
        r["links"] = [{"key": a["key"], "name": a["name"]} for a in cal_a.get(WEAPON_CAL[r["key"]], [])]
    elif r["key"] in AMMO_CAL:
        r["links"] = [{"key": w["key"], "name": w["name"]} for w in cal_w.get(AMMO_CAL[r["key"]], [])]
    else:
        r["links"] = []

# custody module seed: tracked assets, soldier-code records, custody + audit (trims legacy counts)
CUSTODY = build_seed(out_items)
def build_groups(items):
    """Resolve GROUPS into catalogue keys; every line must land in exactly one sub-group."""
    seen, out = {}, []
    for gk, gl, subs in GROUPS:
        g = {"key": gk, "label": gl, "subs": []}
        for i, (sl, rules) in enumerate(subs):
            keys = [it["key"] for it in items if any(it["type"] == t and (sb is None or it["sub"] == sb) for t, sb in rules)]
            for k in keys:
                assert k not in seen, f"{k} is in both {seen[k]} and {gk}/{sl}"
                seen[k] = f"{gk}/{sl}"
            g["subs"].append({"key": f"{gk}-{i}", "label": sl, "items": keys})
        out.append(g)
    missing = [it["key"] for it in items if it["key"] not in seen]
    assert not missing, f"catalogue lines missing from GROUPS: {missing}"
    return out

payload = {"items": out_items, "types": TYPES, "subOrder": SUBS, "policy": CATEGORY_POLICY, "custody": CUSTODY,
           "groups": build_groups(out_items)}
DATA = json.dumps(payload, ensure_ascii=False)
GEO_PATH = os.path.abspath(os.path.join(HERE, "..", "maps", "india.min.json"))
GEO = open(GEO_PATH, encoding="utf-8").read() if os.path.exists(GEO_PATH) else "null"
EMB_PATH = os.path.abspath(os.path.join(HERE, "..", "emblem", "emblem_datauri.txt"))
EMBLEM = open(EMB_PATH, encoding="utf-8").read().strip() if os.path.exists(EMB_PATH) else ""
tpl = open(os.path.join(HERE, "template_site.html"), encoding="utf-8").read()
html = (tpl.replace("/*__DATA__*/null", DATA).replace("/*__GEO__*/null", GEO)
        .replace("__EMBLEM__", EMBLEM).replace("__ASOF__", "24 NOV 2026"))
open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(html)
mb = round(os.path.getsize(os.path.join(OUTDIR, "index.html")) / 1024 / 1024, 2)
print("wrote", mb, "MB |", len(out_items), "items | missing photos:", missing)
