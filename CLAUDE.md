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
- Data reaches the page as `DATA = {items, types, subOrder, policy, custody, groups}`.

## Custody module conventions

- **Codes only.** Soldiers have a Soldier ID (`SOL-0001`) and a service code (`SC-12345`). Never add
  personal names or photos.
- Legacy codes such as `RFL-4107` are **equipment issue codes**, not soldiers. They form the bulk roster.
- **`Store` is the only source of truth** for soldiers, assets, custody and audit. Views read through
  `Store.*` and change data only through its mutators (`issue`, `issueBatch`, `returnAsset`, `setAssetStatus`,
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
- Explosives (`sealed`) and ammunition (`bulk`) must never get a soldier-level issue path.
- **Multi-item issue** (`Store.issueBatch`, form `multi`): one submission creates one independent custody
  record per asset (own ID, audit events and status), never a shared record. Every asset goes through
  the single-issue rules (`issue` with `_dry`); any failure rejects the whole batch, with per-asset
  reasons in `errors.items`. `batchId` (`BAT-0001`) only groups the records. `+ New Custody Record`
  and soldier Assign open the multi form; an asset's own Assign keeps the single form.
- Record pages open in the shared modal through a view stack: `sheetOpen(view, reset)`, `sheetBack()`,
  `renderSheet(keep)`. Add a new record or form type by adding a renderer to `VIEW_RENDER` (and to
  `FORMS` for forms). Navigation uses `data-go="kind:id"` and actions use `data-act`, both handled by
  delegated listeners.

## App shell (UX conventions)

- **One area at a time:** `section.view[data-view]` with hash routing (`#overview` `#catalogue`
  `#assets` `#soldiers` `#custody` `#audit`), set up in `wireShell()` and `showView()`. Primary
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
