# Regiment Management — Design

Date: 2026-11-26 · Status: implemented

## Intent

Group soldiers into regiments so that each soldier has exactly one current regiment. Keep the data
normalised: no duplicate soldiers, ID-based links, full history. Existing saved demo data must survive.

## Data model (inside `Store`, persisted in `armoury-custody-v1`)

| Table | Key fields |
|---|---|
| `regiments` | `id` (`REG-01`, immutable), `code` (unique, immutable after create), `name` (unique), `description`, `status` Active/Inactive, `createdAt`, `updatedAt` |
| `soldiers` (existing) | adds `regimentId`, the current regiment (null = Unassigned) |
| `memberships` | `id` (`MEM-00001`), `soldierId`, `regimentId`, `startedAt`, `endedAt` (null = current), `kind` (Migration · Assignment · New soldier · Transfer · Correction), `authorizedById`, `reason`, `by`, `endedBy`, `endReason` |

**Invariant:** each soldier has at most one open membership, and `soldier.regimentId` equals its
regiment. `Store.integrity()` checks this plus regiment/service-code uniqueness and every reference
(memberships → soldiers and regiments, custody → soldiers).

## Rules (enforced in Store)

- `createRegiment`: code must be 3–16 characters (A–Z, 0–9, hyphen) and is unique without regard to
  case. The name is also unique. Status must be valid.
- `updateRegiment`: needs a reason and at least one change. It cannot deactivate a regiment that still
  has members.
- `assignSoldier`: only for a soldier with no current regiment. Assigning someone who is already in a
  regiment is rejected with "use Transfer".
- `transferSoldier`:
  - needs a valid, Active destination that differs from the current regiment;
  - the type is Transfer or Correction;
  - closes the old membership and opens a new one, both in a single atomic write.
- `createSoldier` needs a valid, Active `regimentId`. It creates the soldier record and its membership
  together, with rollback.
- **Authorisation:** assign and transfer need an Active officer who isn't the soldier, plus a reason.
  Every write records the desk operator.
- **Audit:** "Regiment created / updated / deactivated / reactivated" on the Regiment. "Assigned to
  regiment / Transferred / Membership corrected" on the Soldier. "Soldier assigned / transferred in /
  out" and "Membership corrected (in/out)" on the regiments involved. Reasons carry the authorising
  officer's code and the membership ID.

## Migration (m1)

- **Where the demo data lives:** the demo regiments and the seed's soldier → regiment map are added to
  the seed **after** its hash. Existing saved state therefore still matches the build and is not reset.
- **When it runs:** `migrate()` runs on every load and after reset. It saves only when something changed.
- **What it does:**
  1. Adds any demo regiment missing by ID or code.
  2. Gives each soldier without an open membership one: seeded soldiers by ID **and** matching service
     code, others by unit name.
  3. Leaves a soldier it can't place Unassigned. The Regiments page lists them with an Assign action.
- **Never:** it doesn't overwrite an existing membership or auto-resolve a conflict.
- **Idempotent:** a second run returns 0 changes. The version is stored in `T.mig`.

## UI

- **Sidebar › Regiments:** a table with code, name, soldier, active and holding-equipment counts, status,
  and Updated. It has status chips, search, ＋ Add soldier / Open per row, ＋ New regiment, and an
  Unassigned banner.
- **Regiment record:**
  - details, overview tiles, current soldiers (with Transfer), membership history and audit timeline;
  - Add soldier / Edit regiment.
- **Add soldier:**
  - The lookup lists every existing soldier with their current regiment ("will be a transfer").
  - Soldiers already in this regiment are disabled.
  - *＋ Create new soldier in CODE* opens the soldier form with the regiment fixed.
  - Officer and reason are required, and the change is reviewed before it is saved.
- **Soldiers:** a Regiment column with the Unassigned badge, a regiment filter, and search by regiment
  code or name. The soldier record shows the regiment, *Transfer / Assign regiment*, and Regiment History.
- **Audit:** a Regiment entity filter.

## Limitations

- **Actor:** recorded as the single demo desk operator (`ADM-DESK-01`) plus the authorising officer.
  There are no user accounts or roles.
- **Regiment codes** can't be edited after creation, so IDs and codes stay stable.
- **Demo regiments** are illustrative, not real Indian Army organisational data.
