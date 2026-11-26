# EkBharat Armoury — notes for Claude

Indian Armed Forces–themed equipment inventory and custody dashboard. All data is illustrative game data.

## Architecture (keep it this way)

- One self-contained page. Edit `build/template_site.html` (vanilla JS + D3, no framework, no
  TypeScript, no router, no bundler), then run `cd build && python gen_site.py` and copy
  `out/index.html` over `/index.html`. Never edit `/index.html` by hand: it is ~5 MB of embedded photos.
- `build/equip_items.py` is the catalogue: `TYPES` (categories), `SUBS` (sub-category order) and
  `CATEGORY_POLICY` (`tracked` / `bulk` / `sealed`). To add a category, add one line to each, and map it in
  `GROUPS` (the custody browser hierarchy). `gen_site.py` fails the build if any catalogue line is in no
  group or in two.
- `build/custody_seed.py` deterministically generates the custody demo seed and trims each tracked
  line's legacy count (see the quantity rules below). Its hash versions the saved browser state.
  Demo regiments (`DEMO_REGIMENTS`, illustrative only) are added **after** the hash, so adding regiments
  never invalidates saved state.
- Data reaches the page as `DATA = {items, types, subOrder, policy, custody, groups, assignRules}`.
- Assignment eligibility lives only in `equip_items.py`, and the page reads it only through
  `Store.eligibility(line, target)` (and `issueBlock(asset, target)`). Never test category names in UI code.
  - `ASSIGNMENT_CLASS` is the user's fixed classification (don't reclassify without being asked):
    - `individual` (Individual Soldier only): weapons, helmets, armor, plates, nightvision.
    - `team` (Team only): explosives, ammunition, comms, armoured.
    - The reasons shown are exactly "Individual Soldier only — Team assignment unavailable." and
      "Team only — Individual assignment unavailable."
  - How a line is held still follows its custody policy: tracked → `"asset"` custody; bulk/sealed → `"stock"`
    allocation (team only).
  - Categories not in `ASSIGNMENT_CLASS` (melee, attachments, drones, artillery) fall back to `ASSIGNMENT_RULES`
    (policy → holder → mode).

## Custody module conventions

- **Codes only.** Soldiers have a Soldier ID (`SOL-0001`) and a service code (`SC-12345`). Never add
  personal names or photos.
- Legacy codes such as `RFL-4107` are **equipment issue codes**, not soldiers. They form the bulk roster.
- **`Store` is the only source of truth** for soldiers, assets, custody and audit. Views read through
  `Store.*` and change data only through its mutators (`issue`, `issueBatch`, `returnAsset`, `createRegiment`, `updateRegiment`,
  `assignSoldier`, `transferSoldier`, `setAssetStatus`,
  `addCorrection`, `createSoldier`, `setSoldierStatus`, `registerAsset`, `reset`). Each mutator
  validates, writes audit events, saves to `localStorage["armoury-custody-v1"]`, then emits. The single
  subscriber in `wireCustody()` re-renders everything. Don't keep per-view copies of the data.
- Records point to each other by ID (`soldierId`, `assetId`, `catalogueKey`, `authorizedById`); names
  and codes are looked up when rendering. The current custodian is derived from the one Active custody
  record and is never stored on the asset.
- **Quantity rules live only in `Store.qty(w)`:** total assigned = `legacyAssigned` + active tracked
  custody. `recompute()` writes that into `w.assigned`, so cards, KPIs and alerts all use it. A tracked
  asset is never also counted in the legacy figure.
- Business rules are enforced in `Store`, not just the UI: one active custody per asset; only Active
  soldiers receive custody; only Active officers authorise; retired, in-maintenance and
  inspection-pending assets cannot be issued; closed records are immutable (corrections are appended);
  tags, serials and service codes are unique.
- Explosives (`sealed`) and ammunition (`bulk`) must never get a soldier-level issue path; they reach teams only as authorised stock allocations.
- **Regiments** are a separate table (`T.regiments`, IDs `REG-01`, unique codes). `soldier.regimentId` is the
  current regiment and must equal the soldier's single open record in `T.memberships` (the history:
  `startedAt`/`endedAt`, kind, authoriser, reason). Never edit `regimentId` directly: use `assignSoldier`
  (only for unassigned soldiers), `transferSoldier` (kind `Transfer` or `Correction`, closes the old record),
  or `createSoldier` (which needs `regimentId` and creates the soldier and membership atomically).
  Changes need an Active officer who isn't the soldier, plus a reason. Inactive regiments take no soldiers
  and can only be deactivated when empty. Composite writes go through `atomic()` (snapshot rollback).
  `Store.integrity()` lists any broken invariant; it should return `[]`.
- **Teams** (`T.teams`, `TEM-001`): each belongs to one regiment, and its code is unique within that regiment. `soldier.teamId`
  is the open record in `T.teamMemberships`, and it must be a team of the soldier's current regiment. Change it only
  with `setSoldierTeam` (needs an officer and a reason). `transferSoldier` closes the team membership in the same
  atomic write.
- **Custody targets:** a custody record has `targetType` `Soldier` (`soldierId`) or `Team` (`teamId`). Records
  with no `targetType` are legacy Soldier records. Never create a placeholder soldier for a team. Display the
  holder with `holderLink(c)` / `Store.holderCode(c)`, not `solLink(c.soldierId)`. `Store.assign(f)`
  (`issueBatch` wraps it) validates every asset with the single-issue rules plus the regiment/team/soldier
  context, then writes everything atomically.
- **Team stock** (`T.allocations`, `ALC-00001`): quantity ledger for `stock` lines, Team holders only. It needs
  an officer and `authRef`, can never exceed `qty(w).reserve`, and supports partial `returnStock`.
  `Store.qty`: total assigned = legacy + active tracked custody + outstanding allocations.
- **Migration:** `migrate()` (version `T.mig`, currently 3; m2 = `migrateTeams()`, m3 = demo Gorkha regiment `REG-90` + team `TEM-090`) runs on every load and on reset. It is idempotent:
  it adds missing demo regiments and gives soldiers without a membership one (seed ID + service code, then
  unit name). Anyone it can't place stays Unassigned and is listed on the Regiments page with an Assign
  action. Bump `MIGRATION` and add a guarded step for future schema changes; never reset data to migrate.
- **Assignment form** (`Store.assign`, form `multi`): Regiment → Individual Soldier (a soldier of that regiment)
  | Team (a team of that regiment) → browser → review. The browser shows only categories eligible for the
  destination; the rest are listed, not selectable, with the short reason. One submission creates one custody record per asset and one allocation per
  stock line, never a shared record. Any failure rejects the whole submission, with per-item reasons in
  `errors.items`. `batchId` (`BAT-0001`) only groups the records. Every Assign button (asset, soldier,
  team, + New Custody Record) opens this form with the path preset. There is no separate single-soldier form.
- Record pages open in the shared modal through a view stack: `sheetOpen(view, reset)`, `sheetBack()`,
  `renderSheet(keep)`. Add a new record or form type by adding a renderer to `VIEW_RENDER` (and to
  `FORMS` for forms). Navigation uses `data-go="kind:id"` and actions use `data-act`, both handled by
  delegated listeners.

## App shell (UX conventions)

- **One area at a time:** `section.view[data-view]` with hash routing (`#overview` `#catalogue`
  `#assets` `#soldiers` `#regiments` `#custody` `#audit`), set up in `wireShell()` and `showView()`. Primary
  navigation is the sidebar `#appnav`. Catalogue filters (`#sbfilters`) and the top-bar search and sort
  (`.tb-cat`) appear only when `body[data-view="catalogue"]`.
- Above 900px the sidebar collapses to an icon rail (`.app.collapsed`, saved in `armoury-sidebar`).
  At 900px and below it becomes a drawer (`.app.drawer`, `#menubtn`, `#scrim`).
- Workspace tables use `.rtable`. Call `labelTables()` after rendering rows: below 700px rows become
  labelled two-column grids, and between 701 and 1180px secondary columns are hidden.
- Forms with a review step: in `FORMS`, an entry with `confirm()` first calls the Store mutator with
  `_dry:true` (validate only), then shows `.fconfirm`. Lookups list every record, with ineligible ones
  disabled and the reason shown.
- Design notes: `docs/superpowers/specs/2026-11-26-custody-ux-design.md`.

## Storage keys

`armoury-theme`, `armoury-reorders`, `armoury-custody-v1`, `armoury-sidebar`. *Reset demo data* (Audit History) clears only the custody key.

## Verify after changes

Serve with `python -m http.server 8787` and open `/out/index.html`. Check the console is clean, and run
issue → return → history → audit → reload (persistence) → reset. Compare the KPI totals with the
previous build: they should change only through custody transactions or catalogue edits.
