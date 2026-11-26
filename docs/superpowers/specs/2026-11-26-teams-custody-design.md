# Regiment → Team → Soldier Equipment Assignment — Design

Date: 2026-11-26 · Status: implemented

## Intent

Make regiment and team the context for equipment accountability. Equipment can be held by a team, or by
one soldier of that team. Assignment starts from that context, not from a bare soldier lookup.

## Data model

| Table | Key fields |
|---|---|
| `teams` | `id` (`TEM-001`), `code` (unique **within** its regiment), `name`, `regimentId`, `status`, `createdAt`, `updatedAt` |
| `teamMemberships` | `id` (`TMM-00001`), `soldierId`, `teamId`, `regimentId`, `startedAt`, `endedAt`, `kind`, `authorizedById`, `reason`, `endReason` |
| `soldiers` | adds `teamId`, the current team (optional; must be in the soldier's current regiment) |
| `custody` | adds `targetType` (`Soldier` or `Team`) and `teamId` for team records (`soldierId` is null). Also `orgRegimentId` and `orgTeamId`, a snapshot of the context at issue. Legacy records have no `targetType` and read as Soldier records. |
| `allocations` | `id` (`ALC-00001`), `catalogueKey`, `targetType: "Team"`, `teamId`, `regimentId`, `qty`, `returnedQty`, `status` (Active/Returned), `authorizedById`, `authRef`, `reason`, `by`, `batchId`, `returns[]` |

Display codes for teams are `REGIMENT/TEAM`, for example `DEMO-ALPHA/A-COY`.

## Assignment policy (single source)

Both `ASSIGNMENT_CLASS` and `ASSIGNMENT_RULES` live in `build/equip_items.py` and are read only through
`Store.eligibility(line, target)`.

**Destination classification** (`ASSIGNMENT_CLASS`, the user's exact rules, 2026-11-26):

| Class | Categories | Individual Soldier | Team |
|---|---|---|---|
| Individual only | weapons, helmets, armor, plates, nightvision | asset custody | "Individual Soldier only — Team assignment unavailable." |
| Team only | explosives, ammunition (stock), comms (asset), armoured (stock) | "Team only — Individual assignment unavailable." | asset custody or stock allocation (officer + authorisation reference) |

The user's fifth team-only class, "shared tools and support equipment", has no matching catalogue
category yet.

**Unclassified categories** keep the policy fallback (`ASSIGNMENT_RULES`):

| Category | Policy | Individual Soldier | Team |
|---|---|---|---|
| melee | tracked | asset custody | asset custody |
| attachments, drones, artillery | bulk | not allowed | stock allocation |

## Rules (Store)

- **`assign` (one submission):**
  - It creates one custody record per asset and one allocation per stock line, all or nothing.
  - Every asset uses the single-issue rules: one active holder, Available status, dates, and an Active
    officer who isn't the recipient.
  - It also checks context: the team must belong to the chosen regiment; an individual soldier must be
    Active and in that regiment and team; the team must be Active.
  - Stock lines must be `stock`-eligible for the target, whole numbers, and at most `qty(w).reserve`.
    They also need `authRef`.
- **`returnStock`:** a partial or full return of a stock allocation. History is kept in `returns[]`.
- **Team changes:**
  - `createTeam` / `updateTeam`: deactivation needs no members, team custody or allocations.
  - `setSoldierTeam`: only to a team of the soldier's own regiment, with officer and reason.
  - `transferSoldier` (regiment) closes the open team membership in the same write.
- **Quantities:** total assigned = legacy + active tracked custody + outstanding allocations. All views
  and KPIs go through `Store.qty`.
- **Audit:** every write records ID, target type and ID, asset or stock line, quantity, actor, timestamp,
  officer code, authorisation reference and reason. The audit entity types are Custody, Asset, Soldier,
  Team, Allocation and Regiment.

## Migration m2 (`migrateTeams`)

- **Demo teams:** 8 teams, one per demo unit, inside that unit's regiment. They are added only where the
  regiment exists and the code is free.
- **Team membership:** a soldier joins a team only when the unit matches **and** the team is in the
  soldier's current regiment. Soldiers transferred across regiments are therefore left with no team, not
  put in a team of another regiment.
- **Safe:** it creates no custody records and changes no counts. It is idempotent, its version is stored
  in `T.mig = 2`, and the demo teams are added after the seed hash so saved state is never reset.

## UI

- **New Custody Record:**
  1. Regiment (inactive regiments are disabled with a reason).
  2. Assign to: Individual Soldier or Team (cards; disabled with a reason when the regiment has no
     Active soldiers or teams).
  3. Individual opens a soldier lookup limited to that regiment. Team opens a select limited to that
     regiment's teams.
  4. The category browser. Only categories eligible for the destination can be browsed; the others
     are listed with the short reason. Stock lines get a quantity input.
  5. The selection panel (assets plus stock lines).
  6. Authorisation, including the reference for stock.
  7. Review, with remove buttons on every item.

  Assign buttons on assets, soldiers and teams preset this path.
- **Team record:** members (with Change team), team custody assets (with Return), stock allocations
  (with Return stock), history, former members and audit. The regiment record lists its teams, and the
  Regiments page has a Teams panel.
- **Soldiers:** team shown under the regiment, Team field and Team History on the soldier record, and
  Assign / Change team.
- **Holders everywhere:** the Custody, Asset Register and item sheets show the holder (soldier or team).
  Bulk item sheets list team allocations.

## Limitations

- **Actor:** recorded as the single demo desk operator plus the approving officer; there are no user
  accounts or roles.
- **Regiment-level custody** is not implemented; teams are the custody unit.
- **Team-to-team transfers** of an asset or allocation are done as a return followed by a new
  assignment, which keeps both records.
- **Transfers:** a soldier moved to another regiment has no team until one is assigned.
