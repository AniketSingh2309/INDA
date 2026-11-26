# -*- coding: utf-8 -*-
"""Deterministic demo seed for the custody module (soldier codes only, no names).

build_seed(items) mutates the generated catalogue records in place:
  - sets rec["tracked"] (number of individually tracked assets on that line)
  - sets rec["legacyAssigned"] = original assigned - seeded active custodies, and trims
    rec["codes"] to that many legacy issue codes, so Total assigned (legacy + active custody)
    equals the original figure at seed time and no unit is counted twice.
and returns the seed tables {soldiers, assets, custody, audit, seq, hash}.
All values are illustrative game data.
"""
import datetime, hashlib, json

TODAY = datetime.date(2026, 11, 24)
OPERATOR = "ADM-DESK-01"

# catalogue key -> (asset count, tag prefix, serial prefix)
TRACKED_LINES = {
    "insas":           (10, "INSAS", "IN1B1"),
    "ak203":           (10, "AK203", "AK2"),
    "svd":             (8,  "SVD",   "SVD"),
    "glock":           (10, "G17",   "G17"),
    "ballistichelmet": (12, "BCH",   "BCH"),
    "nvg_bino":        (10, "PNVG",  "NVG"),
}

RANKS_OR = ["Sepoy", "Lance Naik", "Naik", "Havildar", "Naib Subedar", "Subedar"]
RANKS_OFF = ["Lieutenant", "Captain", "Major"]
OFFICER_RANKS = set(RANKS_OFF)
ARMS = [("Infantry", "Rifleman"), ("Infantry", "Section Commander"), ("Infantry", "Designated Marksman"),
        ("Signals", "Signaller"), ("Armoured Corps", "Crewman"), ("Artillery", "Gun Number"),
        ("EME", "Armourer"), ("Army Medical Corps", "Nursing Assistant")]
UNITS = ["1 Inf Bn · A Coy", "1 Inf Bn · B Coy", "1 Inf Bn · C Coy", "2 Inf Bn · HQ Coy",
         "2 Inf Bn · D Coy", "Recce Pl", "Sig Coy", "EME Wksp Det"]


def _h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def _d(days_ago):
    return (TODAY - datetime.timedelta(days=days_ago)).isoformat()


def _ts(days_ago, hh=9, mm=0):
    return f"{_d(days_ago)}T{hh:02d}:{mm:02d}:00"


def build_seed(items):
    by = {r["key"]: r for r in items}
    soldiers, assets, custody, audit = [], [], [], []
    seq = {"SOL": 0, "AST": 0, "CUS": 0, "AUD": 0}

    def nid(p, w):
        seq[p] += 1
        return f"{p}-{seq[p]:0{w}d}"

    def aud(etype, eid, action, prev, new, ts, reason=""):
        audit.append({"id": nid("AUD", 5), "entityType": etype, "entityId": eid, "action": action,
                      "prev": prev, "next": new, "by": OPERATOR, "ts": ts, "reason": reason})

    # ---- 40 soldiers: 6 officers + 34 other ranks; 2 on leave, 2 inactive ----
    for i in range(40):
        officer = i < 6
        rank = RANKS_OFF[i % 3] if officer else RANKS_OR[_h(f"r{i}") % len(RANKS_OR)]
        arm, desig = ARMS[_h(f"a{i}") % len(ARMS)]
        if officer:
            desig = "Company Commander" if rank == "Major" else ("Platoon Commander" if rank == "Lieutenant" else "Quartermaster")
        status = "Inactive" if i in (37, 39) else ("On Leave" if i in (22, 31) else "Active")
        sid = nid("SOL", 4)
        code = f"SC-{24100 + i * 7 + (_h(f'c{i}') % 5)}"
        created = _ts(400 + i, 10)
        soldiers.append({"id": sid, "serviceCode": code, "rank": rank, "department": arm,
                         "unit": UNITS[_h(f"u{i}") % len(UNITS)], "designation": desig,
                         "status": status, "createdAt": created, "updatedAt": created})
        aud("Soldier", sid, "Record created", None, status, created, "Demo personnel register")
    officers = [s for s in soldiers if s["rank"] in OFFICER_RANKS and s["status"] == "Active"]
    holders = [s for s in soldiers if s["rank"] not in OFFICER_RANKS and s["status"] == "Active"]
    past = [s for s in soldiers if s["status"] != "Active"]  # inactive / on-leave hold history only

    hi = 0  # rotating holder index (lets one soldier hold several assets)
    for key, (n, tagp, serp) in TRACKED_LINES.items():
        rec = by[key]
        line_assets = []
        for j in range(1, n + 1):
            aid = nid("AST", 4)
            acq = _d(300 + (_h(key + str(j)) % 200))
            a = {"id": aid, "tag": f"EKB-{tagp}-{j:04d}", "catalogueKey": key,
                 "serial": f"{serp}-26-{100000 + _h(serp + str(j)) % 900000:06d}",
                 "condition": "Serviceable", "status": "Available", "acquisitionDate": acq,
                 "docRef": f"CRV/{tagp}/{2025 if j % 2 else 2026}/{(_h(aid) % 900) + 100}",
                 "createdAt": acq + "T08:00:00", "updatedAt": acq + "T08:00:00"}
            assets.append(a); line_assets.append(a)
            aud("Asset", aid, "Asset registered", None, "Available", a["createdAt"], "Receipt voucher " + a["docRef"])

        for j, a in enumerate(line_assets):
            # history: every 3rd asset had a previous, closed custody record
            if j % 3 == 0:
                who = past[(j + hi) % len(past)] if j % 2 else holders[(hi + 11) % len(holders)]
                eff, ret = 240 - j * 3, 120 - j * 2
                cid = nid("CUS", 5)
                custody.append({"id": cid, "soldierId": who["id"], "assetId": a["id"], "type": "Personal Issue",
                                "effectiveDate": _d(eff), "returnDate": _d(ret), "status": "Closed",
                                "authorizedById": officers[j % len(officers)]["id"], "issuedBy": OPERATOR,
                                "receivedBy": who["serviceCode"], "remarks": "Annual issue",
                                "returnCondition": "Serviceable", "returnRemarks": "Returned on posting",
                                "returnReceivedBy": OPERATOR, "corrections": [],
                                "createdAt": _ts(eff), "updatedAt": _ts(ret, 15)})
                aud("Custody", cid, "Custody issued", None, "Active", _ts(eff), "Annual issue")
                aud("Custody", cid, "Custody closed", "Active", "Closed", _ts(ret, 15), "Returned on posting · Serviceable")
            # current state: first ~half in active custody, a few non-available states
            if j < (n + 1) // 2:
                who = holders[hi % len(holders)]; hi += 1
                eff = 90 - j * 4 - (_h(a["id"]) % 20)
                cid = nid("CUS", 5)
                custody.append({"id": cid, "soldierId": who["id"], "assetId": a["id"],
                                "type": "Temporary Loan" if j == 1 else "Personal Issue",
                                "effectiveDate": _d(eff), "returnDate": None, "status": "Active",
                                "authorizedById": officers[(j + 2) % len(officers)]["id"], "issuedBy": OPERATOR,
                                "receivedBy": who["serviceCode"], "remarks": "Unit issue", "returnCondition": None,
                                "returnRemarks": None, "returnReceivedBy": None, "corrections": [],
                                "createdAt": _ts(eff), "updatedAt": _ts(eff)})
                a["status"] = "In Custody"; a["updatedAt"] = _ts(eff)
                aud("Custody", cid, "Custody issued", None, "Active", _ts(eff), "Unit issue")
                aud("Asset", a["id"], "Status changed", "Available", "In Custody", _ts(eff), "Issued under " + cid)
            elif j == n - 1:
                a["status"], a["condition"] = "Inspection Pending", "Damaged"
                aud("Asset", a["id"], "Status changed", "Available", "Inspection Pending", _ts(20), "Damage reported at range")
            elif j == n - 2 and key in ("ak203", "nvg_bino"):
                a["status"], a["condition"] = "Under Maintenance", "Unserviceable"
                aud("Asset", a["id"], "Status changed", "Available", "Under Maintenance", _ts(35), "Sent to EME workshop")
            elif j == n - 2 and key == "svd":
                a["status"], a["condition"] = "Retired", "Unserviceable"
                aud("Asset", a["id"], "Asset retired", "Available", "Retired", _ts(60), "Beyond economical repair")

        active = sum(1 for c in custody if c["status"] == "Active" and c["assetId"] in {x["id"] for x in line_assets})
        legacy = rec["assigned"] - active
        assert legacy >= 0 and n + legacy <= rec["arrived"], f"tracked sample does not fit {key}"
        rec["tracked"] = n
        rec["legacyAssigned"] = legacy
        rec["codes"] = rec["codes"][:legacy]

    for r in items:
        r.setdefault("tracked", 0)
        r.setdefault("legacyAssigned", r["assigned"])

    audit.sort(key=lambda e: (e["ts"], e["id"]))
    tables = {"soldiers": soldiers, "assets": assets, "custody": custody, "audit": audit, "seq": seq}
    tables["hash"] = hashlib.md5(json.dumps(tables, sort_keys=True).encode()).hexdigest()[:12]
    tables["operator"] = OPERATOR
    # Regiments are added AFTER the hash on purpose: saved browser state keeps matching the seed, and the
    # page's versioned migration (Store.migrate) adds these regiments and memberships to it in place.
    tables.update(build_regiments(soldiers))
    return tables


# Illustrative demo regiments only, not real Indian Army organisational data.
# (id, code, name, description, status, unit prefixes whose soldiers belong to it)
DEMO_REGIMENTS = [
    ("REG-01", "DEMO-ALPHA", "Alpha Regiment (Demo)", "Illustrative demo regiment holding the 1 Inf Bn companies.", "Active", ["1 Inf Bn"]),
    ("REG-02", "DEMO-BRAVO", "Bravo Regiment (Demo)", "Illustrative demo regiment holding the 2 Inf Bn companies.", "Active", ["2 Inf Bn"]),
    ("REG-03", "DEMO-CHARLIE", "Charlie Support Regiment (Demo)", "Illustrative demo regiment for support detachments: recce, signals and EME.", "Active", ["Recce Pl", "Sig Coy", "EME Wksp Det"]),
    ("REG-04", "DEMO-DELTA", "Delta Reserve Regiment (Demo)", "Illustrative inactive demo regiment with no current members.", "Inactive", []),
    ("REG-90", "DEMO-GORKHA", "Gorkha Regiment (Demo)", "Illustrative demo regiment with one demo team; add soldiers as needed.", "Active", []),
]
# demo teams that do not come from a seeded unit: (id, code, name, regiment id)
EXTRA_TEAMS = [("TEM-090", "A-COY", "A Coy Team (Demo)", "REG-90")]


def build_regiments(soldiers):
    regs, by_unit = [], {}
    for i, (rid, code, name, desc, status, prefixes) in enumerate(DEMO_REGIMENTS):
        ts = _ts(520 - i, 9)
        regs.append({"id": rid, "code": code, "name": name, "description": desc, "status": status, "createdAt": ts, "updatedAt": ts})
        for u in UNITS:
            if any(u.startswith(p) for p in prefixes):
                by_unit[u] = rid
    assert set(by_unit) == set(UNITS), "every demo unit must map to one demo regiment"
    # seeded soldier -> regiment, keyed by ID and checked against the service code during migration
    regiment_of = {s["id"]: {"serviceCode": s["serviceCode"], "regimentId": by_unit[s["unit"]]} for s in soldiers}
    # demo teams: one per demo unit, inside that unit's regiment (codes unique within the regiment)
    teams = []
    for i, u in enumerate(UNITS):
        short = u.split(" · ")[-1]
        code = short.upper().replace(" COY", "-COY").replace(" PL", "").replace(" WKSP DET", "").replace(" ", "-")
        ts = _ts(500 - i, 9)
        teams.append({"id": f"TEM-{i + 1:03d}", "code": code, "name": f"{short} Team (Demo)", "regimentId": by_unit[u],
                      "unit": u, "status": "Active", "createdAt": ts, "updatedAt": ts})
    for tid, code, name, rid in EXTRA_TEAMS:
        ts = _ts(480, 9)
        teams.append({"id": tid, "code": code, "name": name, "regimentId": rid, "unit": None, "status": "Active", "createdAt": ts, "updatedAt": ts})
    return {"regiments": regs, "regimentByUnit": by_unit, "regimentOf": regiment_of, "teams": teams}
