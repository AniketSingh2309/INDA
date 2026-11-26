# Custody UX Refinement — Design

Date: 2026-11-26 · Status: approved (sidebar + one-area-at-a-time), building

## Intent

Make the custody features discoverable and quick for an armoury administrator, without changing the
custody business logic, seed data or quantity calculations. Today Soldiers, Custody and Audit sit
below 102 equipment cards on one long page.

## Decisions (approved)

- **App shell:** a persistent left sidebar is the primary navigation. Items: Overview, Equipment
  Catalogue, Asset Register, Soldiers, Custody Records, Audit History, plus a `＋ New Custody Record`
  quick action at the top.
- **Catalogue filters** (category, delivery status, origin, low stock) live in the sidebar and are
  shown only while the Catalogue is open. Selections persist in memory across navigation.
- **One area at a time.** Hash URLs: `#overview` · `#catalogue` · `#assets` · `#soldiers` ·
  `#custody` · `#audit`. Browser Back/Forward switch areas, and a hash change closes any open sheet.
- **Desktop:** the sidebar collapses to an icon rail (saved in `armoury-sidebar`). **Below 900px:** it
  becomes a slide-out drawer with a ☰ button, a backdrop, and Escape to close.

## My calls

- **Overview:** quick actions (New Custody Record, Register Equipment Asset, Find Soldier, View Active
  Custody), the existing KPIs, a custody stats strip, the pipeline, readiness by category, and the map.
- **Catalogue:** the search and sort controls in the top bar appear only here. Tracked-policy cards
  get a "Manage assets · N available" button that opens the item sheet at its Tracked Assets table.
- **Item sheet:** Custody Control / Tracked Assets moves above the specifications. Each row gets
  Assign (when Available) or Return (when in custody).
- **Asset Register (new view of existing data):** every tracked asset, with status chips, an
  equipment-line filter, search, and an Assign/Return/View action on each row.
- **Soldiers:** a directory table with service code, rank, unit, status, equipment count and custody
  state, plus a View action and status / "holding equipment" filters.
- **Custody Records:** Active · Returned · Returned unserviceable · All, with search and a Return
  button on active rows. The legacy bulk roster moves into a collapsed panel below (progressive disclosure).
- **Audit History:** entity filter and search. *Reset demo data* lives here (system action).
- **Forms:** fields grouped into numbered steps. Lookups list every record but disable ineligible
  ones and show the reason. Choosing a record shows its context. Issue, return and retirement go
  through a review-and-confirm step before saving.
  - To support that step, `Store.issue`, `returnAsset` and `setAssetStatus` take a `_dry` flag:
    validate and return without changing anything. The validation rules themselves are unchanged.
  - Register Equipment Asset can now be started without choosing a line first (a picker in the form).
- **Display only:** custody status `Closed` is shown as **Returned**; the stored value is unchanged.
- **Responsive:** below 700px, tables turn into labelled stacked rows, the KPI grid is 2-up and
  compact, and the top bar wraps without overflow. The cause of the existing horizontal overflow is
  fixed rather than hidden.
- **Feedback:** success toasts (green) and error toasts (red). Everything is synchronous, so there are
  no loading states.

## Unchanged

Store data, validation rules, seed, quantities, reorders, map, theme, storage keys and all element IDs
that existing logic relies on.

## Addendum: multi-item custody (2026-11-26)

- **Hierarchy:** `GROUPS` in `build/equip_items.py` maps every catalogue line (by type and sub-category)
  into Firearms, Protective Equipment, Night Vision & Optical, Communication Equipment, Vehicles,
  Artillery & UAV, Other Equipment, and Restricted Stock. The build fails on a missing or duplicated
  line. No Medical or Field groups were added, because the catalogue has no such lines.
- **Form `multi`:**
  1. Recipient lookup, showing what the soldier already holds.
  2. Browser: group tiles › sub-group tiles › models › assets with checkboxes. A global search covers
     models, categories, tags and serials. A breadcrumb leads back up, and the selection survives
     navigation. A persistent selection panel shows the selected items, each with ✕.
  3. Authorisation, applied to every item.

  The review lists each item (with remove), then *Confirm & create N records*.
- **Store:** `issueBatch` validates each asset with the unchanged single-issue rules. It rejects
  duplicates and anything that isn't a registered asset, so catalogue keys, ammunition and explosives
  can't get in by direct calls either. It writes one record and three audit events per asset, then
  commits once, and restores a snapshot if anything throws. Records carry an optional `batchId`.
- **Restricted lines** stay browsable with their restriction shown, but have no checkboxes.
- **Entry points:** *New Custody Record* and soldier *Assign* open the multi form. An asset's own
  *Assign* keeps the single form, which links to the multi form with that asset preselected.
