# Equipment Custody & Soldier-Code Records — Design

Date: 2026-11-26 · Status: approved direction (Option A), building

## Intent

Extend EkBharat Armoury's existing Equipment Section with a relational, Dynamics 365–style
custody system: soldier records (codes only), equipment catalogue, individually tracked assets,
custody records and an audit trail. One shared data layer is the only source; every view derives
from it. Admin record-keeping only — not tactical/operational distribution.

## Goals / non-goals / anti-goals

- **Goals:** ~40 soldier records, ~60 tracked assets on 6 catalogue lines, issue/return workflow
  with history + audit, duplicate-active-custody prevention, persistence, reset, all pages in sync.
- **Non-goals:** backend, router, TypeScript, React, new build system, per-unit records for the
  thousands of bulk units, soldier names/photos.
- **Anti-goals:** double-counted quantities; aggregate figures changing at load with no transaction;
  any soldier-level issue path for explosives or ammunition; copies of the same data per page.

## Constraints (from the project)

- One self-contained page: `build/template_site.html` (vanilla JS + D3) filled by `build/gen_site.py`
  from `build/equip_items.py`; promoted to `/index.html`.
- Codes-only rule (README): soldiers have a Soldier ID + service code; no names, no photos.
- Existing storage keys stay: `armoury-reorders`, `armoury-theme`. New key: `armoury-custody-v1`.
- Legacy codes like `RFL-4107` are **equipment issue codes**, not soldiers; they stay as the bulk roster.

## Approaches considered

- **A. Tracked sample bolted onto aggregate counts — chosen.** Small, honest about scale, keeps
  existing figures, architecture ready for more tracked lines.
- B. Convert ~15,000 legacy codes into soldiers — rejected: thousands of fake records, still
  one item per "soldier".

## Entities (stable IDs, foreign keys only — names resolved by lookup)

| Entity | Key | Fields |
|---|---|---|
| Category | `type` key (e.g. `weapons`) | label, `policy`: `tracked` · `bulk` · `sealed` |
| Catalogue (existing item) | `key` (e.g. `insas`) | existing fields + `type` → Category, `tracked` flag, `legacyAssigned` |
| Soldier | `SOL-0001` | `serviceCode` (unique, e.g. `SC-24107`), rank, arm/department, unit, designation, status (`Active` · `On Leave` · `Inactive`), createdAt, updatedAt |
| Asset | `AST-0001` | `tag` (unique, e.g. `EKB-INSAS-0001`), `catalogueKey` → Catalogue, serial (unique), condition, status, acquisitionDate, docRef, createdAt, updatedAt |
| Custody | `CUS-00001` | `soldierId` → Soldier, `assetId` → Asset, type (`Personal Issue` · `Temporary Loan`), effectiveDate, returnDate, status (`Active` · `Closed`), `authorizedById` → Soldier (officer), issuedBy, receivedBy, remarks, returnCondition, returnRemarks, corrections[], createdAt, updatedAt |
| Audit | `AUD-00001` | entityType, entityId, action, prev, next, by, ts, reason |

```
Category 1──* Catalogue 1──* Asset 1──* Custody *──1 Soldier
                                  └── ≤1 Active Custody
Every mutation ──> 1..n Audit events
```

Current custodian of an asset = the one `Active` custody row for it (derived, never stored on the asset).
Manufacturer stays the existing `origin` text field (out of scope to normalise).

## Category policy

- `tracked` — personal-issue categories (weapons, melee, helmets, armor, plates, nightvision,
  comms). Only these may have Asset rows / custody.
- `bulk` — unit-issue stock (ammunition, attachments, drones, armoured, artillery). Restricted stock
  shown as today; no custody workflow.
- `sealed` — explosives: "Sealed restricted stock · authorised store custody only". No custody UI,
  and the service layer rejects any custody/asset for these categories.

Policy lives in `TYPES` in `equip_items.py` (3rd tuple element). Adding a category = one line there.
New category **Communications** (`comms`, tracked) with two radio lines (photo-pending placeholder,
bulk counts, no tracked sample yet).

## Tracked sample (seed, generated deterministically in `build/custody_seed.py`)

| Line | Assets | Spare reserve before (arrived − assigned) |
|---|---|---|
| INSAS (`insas`) | 10 | 48 |
| AK-203 (`ak203`) | 10 | 18 |
| SVD (`svd`) | 8 | 9 |
| Glock 17 (`glock`) | 10 | 12 |
| Ballistic Combat Helmet (`ballistichelmet`) | 12 | 60 |
| Passive NV Goggle (`nvg_bino`) | 10 | 200 |

Seed also creates ~40 soldiers (a few `On Leave`/`Inactive`), ~30 active custody records, ~12 closed
historical records, a couple of assets in Inspection/Maintenance and one Retired, plus their audit rows.

## Quantity rules (single implementation: `Store.qty(key)`)

For catalogue line `w`, with `T` = its tracked assets, `A` = those with an Active custody:

- **Total inventory** = `w.arrived` (unchanged by custody; only deliveries change it).
- **Legacy bulk assigned** `B` = `w.legacyAssigned`. At seed: `B = original assigned − A_seed`
  (seeded active custodies are carved *out of* the original figure, so nothing is counted twice),
  and the legacy code list is trimmed to `B` codes.
- **Tracked assigned** = `A`. **Tracked available** = tracked assets with status `Available`.
- **Total assigned** = `B + A` → this is the figure every card, KPI, alert and roster count uses.
  At seed it equals the original `assigned` exactly.
- **Untracked reserve** = `arrived − B − |T|`. Reserve for low-stock alert = `arrived − (B + A)`.
- Precondition (checked in build): `|T| + B ≤ arrived`.

So issuing a tracked asset raises Total assigned by 1; returning it lowers it by 1. Nothing else moves.

KPI "Soldiers Equipped" = legacy issue codes + distinct soldiers holding active custody (my call;
at seed this nets to the original figure because the 30 seeded custodies are held by 30 soldiers).
Custody stats (tracked / in custody / available / inspection+maint. / retired / soldiers holding)
sit on a strip above the custody tabs rather than as a 9th KPI tile, so the 4×2 KPI grid is unchanged.
Retired tracked assets still count in "Total inventory" (it is the delivery figure); they are shown
separately in the item's breakdown.

## Business rules (enforced in the Store, UI only mirrors them)

- Issue requires: asset status `Available`, no Active custody, category policy `tracked`,
  soldier `Active`, authoriser is an Active officer, effective date present and not in the future.
- Return closes the Active row (never deletes): sets returnDate, returnCondition, receivedBy.
  Condition `Serviceable`/`Minor Wear` → asset `Available`; `Unserviceable`/`Damaged` → `Inspection Pending`.
- Asset status transitions: Available ⇄ Inspection Pending ⇄ Under Maintenance; any non-custody
  state → Retired (terminal). `In Custody` only via issue/return.
- Closed custody rows are immutable; the only change is "Add correction note" (appended + audited).
- Unique: soldier serviceCode, asset tag, asset serial. Referential integrity: custody needs existing
  soldier + asset; an asset or soldier with any custody history cannot be deleted (no delete at all).
- Lookups list only valid choices (eligible assets / Active soldiers / Active officers).
- Every mutation writes ≥1 audit row with operator `ADM-DESK-01` (demo operator).

## Persistence

`armoury-custody-v1` = `{v:1, seed:<seed hash>, soldiers, assets, custody, audit, seq}`. Loaded over
the seed if `seed` matches; if the build's seed changed, the stale state is discarded (toast).
**Reset demo data** deletes only this key and reloads the seed; reorders/theme untouched.

## UI (inside the existing page, same visual language)

- **Equipment card:** tracked lines show "Assigned B+A / arrived" and a `TRACKED a/T` chip.
  Explosives card shows "Sealed restricted stock".
- **Detail sheet** gains a view stack with ◂ Back: item → asset → soldier → … . Item view adds
  "Quantity Breakdown" and a "Tracked Assets" subgrid (+ Register asset).
- **Asset view:** identity, catalogue lookup (link), category, manufacturer/origin, tag, serial,
  condition, status, current custodian (link, derived), actions (Issue / Return / status change),
  custody history, audit timeline.
- **Soldier view:** overview, personnel info (codes only), current equipment subgrid, equipment
  history, activity timeline; actions (Issue asset to this soldier, change status).
- **Issue / Return / Correction / New soldier / New asset** forms render as sheet views with inline
  validation errors from the Store.
- **Roster section → tabs:** Roster (legacy, unchanged) · Custody Records (Active / Closed / All views +
  search) · Soldiers (search + status filter + New) · Audit (entity filter + search) · Reset demo data.
- Global search also matches asset tags, serials and soldier service codes of tracked lines.

## Sync

`Store` mutators validate → mutate → audit → persist → `emit()`. One subscriber `refreshAll()`
re-renders KPIs, chart, cards, nav counts, roster tabs and the open sheet view. No view keeps its own copy.

## Build phases

1. Data: `TYPES` policy + comms lines; `custody_seed.py`; `gen_site.py` emits `legacyAssigned`,
   trimmed codes, and `DATA.custody` seed.
2. Store: tables, indexes, `qty()`, validators, mutators, audit, persistence, reset; wire `assigned`
   to `B + A` everywhere it was read.
3. Sheet view stack + item breakdown + tracked assets subgrid + asset & soldier views.
4. Forms: issue, return, status change, correction, new soldier, new asset (searchable lookups).
5. Roster tabs: custody records, soldiers, audit, reset.
6. Verify in browser: full workflow, duplicate prevention, invalid inputs, persistence, reset,
   existing catalogue/reorder/map/theme unaffected, console clean; then promote to `/index.html`.

## Left to the builder

Exact seed values, CSS details within the existing tokens, copy text.
