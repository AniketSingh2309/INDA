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

- **Overview** — KPIs, arrival vs. manufacture pipeline, collapsible *Readiness by Category* chart.
- **Command map** — D3 vector map of India (embedded GeoJSON), no external tiles.
- **Inventory grid** — 100 equipment lines across 12 categories: weapons, ammunition, night-vision,
  drones, armoured vehicles, artillery, attachments, melee, explosives, helmets, armor, plates.
  Every card has a photo and is clickable for full detail (order date, delivery date, batch, depot,
  assignment). **No manufacture date is shown anywhere, by design.**
- **Ammunition** — magazines and bullet boxes with box serial ranges *and* per-bullet serial ranges
  (from-serial → to-serial per box), bullet types matched to each weapon's caliber.
- **Weapon ↔ ammunition cross-links** by caliber.
- **Low-stock & reorder** — restock any low line by choosing an order quantity.
- Theme toggle (dark / light), search, sort — state persisted in `localStorage`.

## Repository layout

```
index.html          Deployed, self-contained dashboard (the deliverable)
build/              Build pipeline
  equip_items.py      100-item equipment catalog (12 categories)
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
