# EkBharat Armoury — Equipment Control Dashboard

A self-contained, offline **equipment / weapon inventory dashboard** themed as an Indian Armed Forces
armoury. Built as a game asset. The dashboard tracks what has arrived versus what is still in
manufacture, which equipment line is assigned to which soldier **code** (codes only — never names),
ammunition box/bullet serial registers, and a national command map.

> ⚠️ **All counts, serial numbers, soldier codes, dates and assignments are illustrative game data —
> not real procurement records.** Equipment reference drawn from
> [globalmilitary.net](https://www.globalmilitary.net/). Photos are from Wikimedia Commons.

## Live page

Open **[`index.html`](index.html)** directly in a browser — it is fully self-contained (all photos,
the India map and the State Emblem are embedded as data URIs, no network required).

To serve it locally:

```bash
python -m http.server 8787
# then open http://127.0.0.1:8787/
```

If GitHub Pages is enabled for this repo (Settings → Pages → deploy from `main` / root), the dashboard
is served from `index.html` automatically.

## What's in the dashboard

- **App shell** — persistent sidebar (Overview, Equipment Catalogue, Asset Register, Soldiers, Custody
  Records, Audit History, ＋ New Custody Record). It collapses on desktop and becomes a drawer on mobile;
  hash URLs keep the browser's Back button working.
- **Overview** — quick actions, KPIs, arrival vs. manufacture pipeline, collapsible *Readiness by Category* chart.
- **Command map** — D3 vector map of India (embedded GeoJSON), no external tiles.
- **Inventory grid** — 102 equipment lines across 13 categories: weapons, ammunition, night-vision,
  drones, armoured vehicles, artillery, attachments, melee, explosives, helmets, armor, plates, communications.
  Every card has a photo and is clickable for full detail (order date, delivery date, batch, depot,
  assignment). **No manufacture date is shown anywhere, by design.**
- **Ammunition** — magazines and bullet boxes with box serial ranges *and* per-bullet serial ranges
  (from-serial → to-serial per box), bullet types matched to each weapon's caliber.
- **Weapon ↔ ammunition cross-links** by caliber.
- **Low-stock & reorder** — restock any low line by choosing an order quantity.
- **Equipment custody** — relational soldier-code records (codes only), individually tracked assets
  (a 60-asset sample on 6 lines), custody issue/return with full history, audit trail, searchable
  lookups, and Custody Records / Soldiers / Audit tabs. *New Custody Record* lets you browse a category
  hierarchy (Firearms › Assault Rifles › INSAS …), pick several assets for one soldier and submit them
  together. Each asset still gets its own custody record, and the batch is all-or-nothing. Explosives
  (sealed) and ammunition (unit-issue) stock can never be issued to a soldier. Design and quantity rules:
  [`docs/superpowers/specs/2026-11-26-equipment-custody-design.md`](docs/superpowers/specs/2026-11-26-equipment-custody-design.md).
- **Regiments** — every soldier belongs to exactly one regiment (illustrative demo regiments are
  seeded). From a regiment, *Add soldier* looks up existing soldiers first (never duplicating them) or
  creates a new one in the same step. Transfers are authorised, reviewed and kept as membership history.
- **Teams & team custody** — each regiment has teams. *New Custody Record* starts from Regiment →
  *Individual Soldier* or *Team* of that regiment. Personal weapons, helmets/armour and night vision go to
  individual soldiers only; explosives, ammunition, radios and vehicles go to teams only (stock lines as
  authorised allocations with officer + authorisation reference and partial returns). A demo *Gorkha Regiment (Demo)* with one team is seeded. Design:
  [`docs/superpowers/specs/2026-11-26-teams-custody-design.md`](docs/superpowers/specs/2026-11-26-teams-custody-design.md).
- Theme toggle (dark / light), search, sort — state persisted in `localStorage`
  (`armoury-theme`, `armoury-reorders`, `armoury-custody-v1`; *Reset demo data* clears only the last).

## Repository layout

```
index.html          Deployed, self-contained dashboard (the deliverable)
build/              Build pipeline
  equip_items.py      102-item equipment catalog (13 categories + CATEGORY_POLICY)
  custody_seed.py     deterministic custody demo seed (soldiers, tracked assets, custody, audit)
  photomap.py         weapon key -> chosen source photo
  gen_site.py         embeds photos + computes data, injects into template -> out/index.html
  template_site.html  master HTML/CSS/JS template with placeholders
  fetch_*.py          Wikimedia photo / GeoJSON fetch helpers
  bgremove.py         (unused) OpenCV background-removal experiment
guns/               Source equipment photos (Wikimedia Commons)
maps/india.min.json India GeoJSON used by the command map
emblem/             State Emblem of India source SVG/PNG + embedded data URI
```

## Rebuilding

```bash
cd build
python gen_site.py          # writes ../out/index.html
cp ../out/index.html ../index.html   # promote to the deployed copy
```

`gen_site.py` reads the catalog, embeds each item's photo (falling back to a same-class photo when an
exact image is unavailable), builds the ammunition serial registers, computes weapon↔ammo caliber
links, and injects everything into `template_site.html`.

## Credits

- Equipment reference: [globalmilitary.net](https://www.globalmilitary.net/)
- Photos & State Emblem: Wikimedia Commons (respective licenses)
- India map data: [udit-001/india-maps-data](https://github.com/udit-001/india-maps-data)
- Charts: D3.js
