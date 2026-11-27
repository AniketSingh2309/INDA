# EkBharat Armoury — Full System Audit

**Date:** 2026-11-27 · **Scope:** entire repository (data model, business logic, persistence, migrations,
UI, access control) · **Method:** static code review of `build/template_site.html`, `build/gen_site.py`,
`build/equip_items.py`, `build/custody_seed.py` + an **executable invariant harness** run against the real
generated `DATA` and `Store` (`build/audit_tests.mjs`).

> All data in the app is illustrative game data (soldier **codes** only, no names/photos). Nothing in this
> audit created real personnel records.

## 1. Architecture assessment

The application is a single self-contained page built by a deterministic Python pipeline. Despite being
vanilla JS, it follows a clean layered design that is **better normalized than most localStorage apps**:

```
UI (render + data-act/data-go delegation)
   │  reads only through Store.*  ·  mutates only through Store mutators
   ▼
Store  (IIFE, single source of truth)
   ├─ validate (per-mutator)                → returns {ok,errors}; _dry for form preview
   ├─ eligibility(line,target) / issueBlock → the ONLY place policy is decided
   ├─ qty(w)                                → the ONLY place quantities are computed
   ├─ atomic(fn)                            → JSON snapshot → run → commit, or rollback on throw
   ├─ audit(...)                            → append-only events on every change
   ├─ migrate()/migrateTeams()             → versioned (T.mig=3), idempotent
   └─ commit() → reindex() + localStorage["armoury-custody-v1"] + emit()
        │
        ▼ one subscriber re-derives every view
```

**Verdict:** the core is sound. Business rules are centralized (not duplicated in the UI), every displayed
quantity derives from `Store.qty`, composite writes are atomic, and migrations are idempotent. The audit
found **no P0/P1 data-integrity defects**. Findings are one P2 (a dead safety net, now wired), one P2
documented limitation (client-only persistence), and minor P3s.

## 2. Entity & relationship map

```
Regiment (REG-xx, unique code)
   ├─1───*─ Team (TEM-xxx, code unique within regiment)
   │           └─1───*─ Soldier.teamId         (open row in T.teamMemberships)
   └─1───*─ Soldier (SOL-xxxx, serviceCode SC-##### unique)
               └─ regimentId = single open row in T.memberships (history: started/endedAt)

Catalogue line (equip_items: key, type→CATEGORY_POLICY tracked|bulk|sealed)
   ├─ tracked →  Individual Asset (AST-xxxx, tag + serial unique)
   │                └─ custody history = all T.custody for assetId; current = the one Active row
   └─ bulk/sealed → Team Stock Allocation (ALC-xxxxx, qty/returnedQty ledger)

Custody record (CUS-xxxxx): targetType Soldier(soldierId) XOR Team(teamId) · assetId · authorizedById
Audit event (AUD-xxxxx): entityType+entityId · action · prev/next · by · ts · reason
```

Referential rules enforced in code: a custody row is Soldier **xor** Team; `teamId`/`regimentId`/`soldierId`/
`assetId`/`catalogueKey`/`authorizedById` must resolve; a soldier's `regimentId`/`teamId` must equal their one
open membership row; a team belongs to one regiment and its soldiers share that regiment; allocations only on
`stock`-eligible lines. **Names are never used as relationship keys** — IDs only; display strings are looked up.

## 3. Findings register

| ID | Sev | Area | Finding | Root cause | Status |
|----|-----|------|---------|-----------|--------|
| F-01 | P2 | Integrity | `Store.integrity()` (orphans, dup IDs/codes, broken refs, double-active custody, over-assignment) was **exported but never called** — the safety net never ran. | No caller; the migration comment "surfaced by integrity()" was aspirational. | **Fixed** — `checkIntegrity()` runs on load and after every mutation (console log always; toast on load or on a newly introduced problem). |
| F-02 | P2 | Persistence | Changing the catalogue/seed changes `SEED.hash`; on next load any stored custody state with a different hash is **replaced by the fresh seed** — user-entered soldiers/assets/custody/allocations are lost. | Saved state is keyed to the exact seed hash (`s.seed===SEED.hash`), by design, so stale demo data can't corrupt a new build. | **Documented** (not changed). Behavior is intentional and the user is warned (`Store.stale` → toast). See Limitations. |
| F-03 | P3 | Catalogue | Two communications lines (`sdr_manpack`, `vhf_handheld`) have no photo → placeholder SVG. | No Wikimedia image fetched for them. | **Deferred** — cosmetic; an honest placeholder is shown (no fake image). |
| F-04 | P3 | Rendering | `esc()` did not escape single quotes. No live sink (all attributes use double quotes), but a latent XSS risk if a single-quoted attribute ever renders user text. | Original regex `[&<>"]`. | **Fixed** — now `[&<>"']` (adds `&#39;`). |

No P0 or P1 findings. Specifically **not** found (verified): orphan records, duplicate identifiers, invalid
foreign references, accidental many-to-many, negative/over-allocated stock, double-counted quantities,
non-atomic multi-step writes, UI-only (unenforced) eligibility, or history overwritten by current-state edits.

## 4. Executable test results

`build/audit_tests.mjs` loads the **real** `DATA` payload and `Store` from the generated `index.html`
(browser globals stubbed; the Store itself has no DOM dependencies) and asserts invariants.

Run: `node build/audit_tests.mjs index.html`

| # | Test | Result |
|---|------|--------|
| T1 | Seed `integrity()` is clean (`[]`) | PASS |
| T2 | Every line reconciles (`reserve=arrived−total`, `total=legacy+active+alloc`, status buckets = asset count) & no negative stock | PASS |
| T3 | Duplicate active custody on one asset blocked | PASS |
| T4 | Atomic batch rollback — one bad item ⇒ zero partial writes | PASS |
| T5 | Team stock allocation persists, references a real team, creates a ledger row | PASS |
| T6 | Return closes the record and frees the asset; quantities reconcile | PASS |
| T7 | Over-allocation (qty > reserve) blocked | PASS |
| T8 | Eligibility enforced in logic: soldier-bulk and tracked-as-stock both rejected | PASS |
| T9 | Duplicate service code blocked; `suggestSoldierCode()` returns a unique code | PASS |
| T10 | `migrate()` idempotent (0 changes on re-run); integrity still clean after all mutations | PASS |
| T11 | State persisted to `armoury-custody-v1` with matching seed hash | PASS |

**11 passed, 0 failed** (after the F-01/F-04 fixes; re-run on the rebuilt `index.html`).

Browser-level check: served via `build/serve.py` on `localhost:8787`, page loads clean and the gated
sign-in + regiment/team custody flows render. Full automated end-to-end browser (click-through) coverage
was **not** run — the logic harness above exercises the same Store paths the UI calls.

## 5. Changes made

| File | Change |
|------|--------|
| `build/template_site.html` | F-01: added `checkIntegrity()` (wired on load + into the Store subscriber). F-04: `esc()` now escapes `'`. |
| `build/audit_tests.mjs` | New — executable invariant harness (11 tests). |
| `CLAUDE.md` | Documented the access-control gate, the integrity watchdog, the `armoury-auth-v1` key, the no-cache `serve.py`, and this audit. |
| `docs/audit/2026-11-27-system-audit.md` | This report. |

**Data model / migrations:** no schema or migration changes were needed — the model is already normalized
and the migration is already versioned and idempotent. **Business rules:** already centralized in `Store`;
none were changed. No business rule, quantity, ID, or seed value was altered.

## 6. Limitations & risks (honest)

- **Client-only, no server.** This is a self-contained page. There is **no** server-side validation,
  authorization, or concurrency control. `localStorage` is single-tab-ish and gives no transactional or
  concurrency guarantees across tabs; `atomic()` protects a single synchronous operation, not two tabs
  writing at once. Any real deployment needs a server as the true source of truth.
- **Access control is demo-grade.** The sign-in/biometric gate verifies identity in the browser but the
  WebAuthn assertion is not verified server-side, and the password is a client-side salted hash. It raises
  the bar for casual misuse; it is not authentication in the security sense. (See CLAUDE.md → Access control.)
- **F-02 seed coupling.** Editing the catalogue/seed intentionally discards divergent saved state (with a
  toast). This protects build integrity but means the demo is not a durable record store. Making saved user
  records survive catalogue changes would require a record-level migration and is deliberately **not** done
  here to avoid risking existing data.

## 7. Preservation confirmation

- **Existing features preserved:** yes. No working feature was removed or rewritten; changes are additive
  (a watchdog call, a one-character `esc` hardening, docs, tests).
- **Existing data preserved:** yes. No seed values, IDs, quantities, or stored-state format changed; the
  seed hash is unchanged by these edits, so any saved `armoury-custody-v1` state still loads.
- **Build pipeline preserved:** yes. Still `python build/gen_site.py` → copy `out/index.html` → root.
