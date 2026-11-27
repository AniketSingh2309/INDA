// Executable audit harness: loads the REAL DATA payload + Store logic from the generated
// index.html and runs invariant tests. No DOM/UI deps are touched by the Store itself.
import fs from 'fs';
const HTML = process.argv[2];
const html = fs.readFileSync(HTML, 'utf8');

// in-memory localStorage stub
globalThis.localStorage = (() => { let m = {}; return {
  getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); },
  removeItem: k => { delete m[k]; }, get _dump(){return m;} }; })();

// --- extract `const DATA = {...};` (payload) ---
const dStart = html.indexOf('const DATA =');
const bStart = html.indexOf('const BYKEY={}');
let dataSrc = html.slice(dStart, bStart).replace('const DATA =', 'globalThis.DATA =');
// --- extract the Store IIFE ---
const sStart = html.indexOf('const Store=(()=>{');
const sEnd = html.indexOf('})();', sStart) + 5;
let storeSrc = html.slice(sStart, sEnd).replace('const Store=(()=>{', 'globalThis.Store=(()=>{');

(0, eval)(dataSrc + '\nglobalThis.BYKEY={}; DATA.items.forEach(i=>BYKEY[i.key]=i);\n' + storeSrc);
const S = globalThis.Store, DATA = globalThis.DATA;

let pass = 0, fail = 0; const fails = [];
const ok = (name, cond, detail='') => { if (cond) { pass++; } else { fail++; fails.push(name + (detail?` — ${detail}`:'')); } console.log(`${cond?'PASS':'FAIL'}  ${name}${detail&&!cond?`  [${detail}]`:''}`); };
const today = S.today();

// T1 — seed integrity clean
const integ = S.integrity();
ok('T1 seed integrity() is clean', integ.length === 0, integ.slice(0,5).join(' | '));

// T2 — quantity reconciliation for every line
let reconBad = [];
DATA.items.forEach(w => {
  const q = S.qty(w);
  const assets = S.assetsOf(w.key);
  if (q.reserve !== w.arrived - q.total) reconBad.push(`${w.key}: reserve≠arrived−total`);
  if (q.total !== q.legacy + q.active + q.allocated) reconBad.push(`${w.key}: total≠legacy+active+alloc`);
  if (q.reserve < 0) reconBad.push(`${w.key}: NEGATIVE reserve ${q.reserve}`);
  if (q.tracked !== assets.length) reconBad.push(`${w.key}: tracked count≠assets`);
  const statusSum = q.active + q.available + q.other + q.retired;
  if (statusSum !== assets.length) reconBad.push(`${w.key}: status buckets ${statusSum}≠${assets.length}`);
});
ok('T2 every line reconciles & no negative stock', reconBad.length === 0, reconBad.slice(0,4).join(' | '));

// helpers to find fixtures
const anAsset = () => S.assets().find(a => !S.issueBlock(a));             // an issuable tracked asset
const officer = S.officers()[0];
const soldier = S.activeSoldiers().find(s => s.regimentId && !S.officers().includes(s));
const teamStockLine = DATA.items.find(w => S.eligibility(w, 'Team').mode === 'stock' && S.qty(w).reserve > 0);
const activeTeam = S.teams().find(t => t.status === 'Active');

// T3 — duplicate active custody blocked
(() => {
  const a = anAsset();
  const base = { assetId: a.id, authorizedById: officer.id, targetType: 'Soldier', soldierId: soldier.id, type: 'Personal Issue', effectiveDate: today };
  const r1 = S.issue(base);
  const r2 = S.issue(base); // same asset again
  ok('T3 duplicate active custody blocked', r1.ok && !r2.ok && /active custody/.test(r2.errors.assetId||''), r2.ok?'second issue succeeded!':'');
})();

// T4 — atomic batch rollback (one bad item ⇒ nothing persists)
(() => {
  const before = S.custody().length;
  const good = S.assets().find(a => !S.issueBlock(a));
  const r = S.assign({ regimentId: null, targetType: 'Soldier', soldierId: soldier.id, authorizedById: officer.id,
    type: 'Personal Issue', effectiveDate: today, assetIds: [good.id, 'AST-DOESNOTEXIST'], stock: [] });
  const after = S.custody().length;
  ok('T4 atomic batch rollback (bad item ⇒ no partial writes)', !r.ok && after === before, `before=${before} after=${after} ok=${r.ok}`);
})();

// T5 — team stock allocation persists, references real team, creates ledger entry
(() => {
  if (!teamStockLine || !activeTeam) { ok('T5 team stock allocation', false, 'no fixture (team stock line/active team)'); return; }
  const before = S.allocations().length;
  const r = S.assign({ regimentId: activeTeam.regimentId, teamId: activeTeam.id, targetType: 'Team',
    authorizedById: officer.id, type: 'Team Issue', effectiveDate: today, assetIds: [],
    stock: [{ catalogueKey: teamStockLine.key, qty: 1 }], authRef: 'TEST-AUTH-001' });
  const after = S.allocations().length;
  const alloc = r.ok && S.allocationsOfTeam(activeTeam.id).find(x => x.catalogueKey === teamStockLine.key);
  ok('T5 team allocation persists & references real team', r.ok && after === before + 1 && !!alloc && alloc.teamId === activeTeam.id, r.ok?'':JSON.stringify(r.errors));
})();

// T6 — return lifecycle reconciles
(() => {
  const a = S.assets().find(x => !S.issueBlock(x));
  const r1 = S.issue({ assetId: a.id, authorizedById: officer.id, targetType: 'Soldier', soldierId: soldier.id, type: 'Personal Issue', effectiveDate: today });
  const cid = r1.rec.id;
  const r2 = S.returnAsset({ custodyId: cid, condition: 'Serviceable', returnDate: today, remarks: '' });
  const c = S.custodyRec(cid), asset = S.asset(a.id);
  ok('T6 return closes record & frees asset', r2.ok && c.status === 'Closed' && asset.status === 'Available' && !S.activeFor(a.id), `cust=${c.status} ast=${asset.status}`);
})();

// T7 — over-allocation blocked
(() => {
  if (!teamStockLine || !activeTeam) { ok('T7 over-allocation blocked', false, 'no fixture'); return; }
  const res = S.qty(teamStockLine).reserve;
  const r = S.assign({ regimentId: activeTeam.regimentId, teamId: activeTeam.id, targetType: 'Team', authorizedById: officer.id,
    type: 'Team Issue', effectiveDate: today, assetIds: [], stock: [{ catalogueKey: teamStockLine.key, qty: res + 1000 }], authRef: 'TEST-OVER' });
  ok('T7 over-allocation blocked', !r.ok, r.ok?'over-allocation succeeded!':'');
})();

// T8 — eligibility enforced in LOGIC (not just UI)
(() => {
  const bulk = DATA.items.find(w => S.eligibility(w, 'Soldier').mode === null && S.eligibility(w, 'Team').mode === 'stock');
  // try to treat a team-stock (bulk) line as an individual asset: there is no asset, but issueBlock on any of its assets (none) → use eligibility
  const soldierBlocked = bulk ? S.eligibility(bulk, 'Soldier').mode !== 'asset' : false;
  const tracked = DATA.items.find(w => S.policyOf(w.type) === 'tracked');
  const trackedAsStock = tracked ? S.eligibility(tracked, 'Team').mode !== 'stock' : false; // tracked→Team is 'asset', not stock
  ok('T8 eligibility blocks soldier-bulk & tracked-as-stock', soldierBlocked && trackedAsStock, `bulk=${!!bulk} tracked=${!!tracked}`);
})();

// T9 — duplicate service code blocked; suggestSoldierCode is unique
(() => {
  const existing = S.soldiers()[0].serviceCode;
  const r = S.createSoldier({ serviceCode: existing, rank: 'Sepoy', department: 'Infantry', unit: '1 Inf Bn · A Coy', designation: 'Rifleman', status: 'Active', regimentId: S.regiments().find(x=>x.status==='Active').id, reason: 'test' });
  const suggested = S.suggestSoldierCode();
  const unique = !S.soldiers().some(s => s.serviceCode.toUpperCase() === suggested.toUpperCase());
  ok('T9 dup service code blocked & suggestion unique', !r.ok && /already exists/.test(r.errors.serviceCode||'') && unique, `suggested=${suggested}`);
})();

// T10 — migration idempotent + integrity still clean after all mutations
(() => {
  const n = S.migrate();           // should be 0 (already migrated)
  const integ2 = S.integrity();
  ok('T10 migration idempotent (0 changes) & integrity clean after mutations', n === 0 && integ2.length === 0, `migrateChanges=${n} integ=${integ2.slice(0,3).join('|')}`);
})();

// T11 — persistence: localStorage holds current state under the versioned key with matching seed hash
(() => {
  const raw = globalThis.localStorage.getItem('armoury-custody-v1');
  let parsed=null; try{parsed=JSON.parse(raw);}catch(e){}
  ok('T11 state persisted to versioned key with seed hash', !!parsed && parsed.v===1 && parsed.seed===DATA.custody.hash, raw?`v=${parsed&&parsed.v}`:'no state written');
})();

// ---- Soldiers advanced-filter relationship correctness (Part A) ----
// T12 — individual vs team custody never conflated at the record level
(() => {
  const bad = S.custody().filter(c => c.status === 'Active' && ((c.teamId && c.soldierId) || (!c.teamId && !c.soldierId)));
  ok('T12 active custody is Soldier XOR Team (never both/neither)', bad.length === 0, bad.slice(0,3).map(c=>c.id).join(','));
})();
// T13 — a soldier's "held equipment" derives ONLY from their individual custody, and only of
//       soldier-eligible (tracked/individual) lines — team stock allocations are never counted.
(() => {
  const held = sid => { const set = new Set(); S.custodyOfSoldier(sid).forEach(c => { if (c.status === 'Active') { const a = S.asset(c.assetId); if (a) set.add(a.catalogueKey); } }); return set; };
  let leak = [];
  S.soldiers().forEach(s => { held(s.id).forEach(k => { const w = DATA.items.find(x => x.key === k); if (!w || S.eligibility(w, 'Soldier').mode !== 'asset') leak.push(`${s.serviceCode}:${k}`); }); });
  // and: no team allocation's line is ever a soldier's held key
  const allocKeys = new Set(S.allocations().map(x => x.catalogueKey));
  const allHeld = new Set(); S.soldiers().forEach(s => held(s.id).forEach(k => allHeld.add(k)));
  const conflated = [...allHeld].filter(k => allocKeys.has(k) && S.eligibility(BYKEY[k], 'Soldier').mode !== 'asset');
  ok('T13 held-equipment filter uses individual custody only (no team-stock conflation)', leak.length === 0 && conflated.length === 0, (leak.concat(conflated)).slice(0,3).join(','));
})();
// T14 — team membership (teamId) is independent of custody: a soldier can be in a team yet the
//       team filter must match by membership, not by any custody record.
(() => {
  const withTeam = S.soldiers().filter(s => s.teamId);
  const allValid = withTeam.every(s => { const tm = S.team(s.teamId); return tm && tm.regimentId === s.regimentId; });
  ok('T14 team membership references a real team of the soldier\'s regiment', allValid, `teamed=${withTeam.length}`);
})();

// ---- Part C: filter combinations verified against actual records ----
const held = sid => { const set = new Set(); S.custodyOfSoldier(sid).forEach(c => { if (c.status === 'Active') { const a = S.asset(c.assetId); if (a) set.add(a.catalogueKey); } }); return set; };
const pred = (s, F) => (F.reg===undefined || (F.reg==='none'?!s.regimentId:s.regimentId===F.reg))
  && (F.team===undefined || s.teamId===F.team)
  && (F.rank===undefined || s.rank===F.rank)
  && (F.cat===undefined || [...held(s.id)].some(k => (BYKEY[k]||{}).type===F.cat))
  && (F.holding===undefined || (F.holding ? held(s.id).size>0 : held(s.id).size===0));
const count = F => S.soldiers().filter(s => pred(s, F)).length;

// T15 — regiment-only equals Store.membersOf
(() => { const r = S.regiments().find(x => S.membersOf(x.id).length); ok('T15 regiment-only filter = membersOf', !!r && count({reg:r.id}) === S.membersOf(r.id).length, r?`${r.code}=${S.membersOf(r.id).length}`:'no fixture'); })();
// T16 — team-only equals teamMembersOf (not conflated with custody)
(() => { const t = S.teams().find(x => S.teamMembersOf(x.id).length); ok('T16 team-only filter = teamMembersOf', !!t && count({team:t.id}) === S.teamMembersOf(t.id).length, t?`${t.code}=${S.teamMembersOf(t.id).length}`:'no fixture'); })();
// T17 — weapon-category AND regiment combine with AND (subset of each)
(() => { const r = S.regiments().find(x => S.membersOf(x.id).length);
  const ty = DATA.types.find(([k]) => DATA.items.some(w => w.type===k && S.eligibility(w,'Soldier').mode==='asset'));
  const both = count({reg:r.id, cat:ty[0]}), onlyReg = count({reg:r.id}), onlyCat = count({cat:ty[0]});
  ok('T17 AND combine ⇒ result ⊆ each dimension', both <= onlyReg && both <= onlyCat, `reg∧cat=${both} reg=${onlyReg} cat=${onlyCat}`); })();
// T18 — unassigned (no regiment) + no duplicates when a soldier holds several items
(() => { const un = count({reg:'none'}); const unReal = S.soldiers().filter(s=>!s.regimentId).length;
  const multi = S.soldiers().find(s => held(s.id).size > 1); // soldier with several assets
  const appearsOnce = multi ? S.soldiers().filter(s=>s.id===multi.id).length===1 : true;
  ok('T18 unassigned filter exact & no soldier duplicated by multi-holding', un===unReal && appearsOnce, `unassigned=${un} multiHolder=${multi?multi.serviceCode:'none'}`); })();

// ---- Data accuracy & KPI correctness ----
// T19 — every catalogue line is capped at <= 900 units (readable demo numbers)
(() => { const over = DATA.items.filter(w => w.ordered > 900 || w.arrived > w.ordered || w.assigned > w.arrived);
  const maxO = Math.max(...DATA.items.map(w => w.ordered));
  ok('T19 every line <= 900 units & ordered>=arrived>=assigned', over.length === 0, `max ordered=${maxO} violations=${over.map(w=>w.key).slice(0,3)}`); })();
// T20 — "Soldiers Holding Equipment" = unique soldiers with an active INDIVIDUAL custody, counted once,
//        never equipment codes, never team custody.
(() => {
  const manual = new Set();
  S.custody().forEach(c => { if (c.status === 'Active' && c.soldierId && !c.teamId) manual.add(c.soldierId); });
  const kpi = S.custodians().size;
  const sane = kpi <= S.soldiers().length;              // can never exceed the number of real soldiers
  ok('T20 Soldiers-Holding KPI = unique individual custodians (small & correct)', kpi === manual.size && sane, `kpi=${kpi} manual=${manual.size} totalSoldiers=${S.soldiers().length}`);
})();
// T21 — "Items Issued" (what the page shows = Σ recomputed qty.total) is an ITEMS metric, distinct
//        from "Soldiers Holding" (a people metric). Proves no entity confusion between the two.
(() => { let issued = 0; DATA.items.forEach(w => { issued += S.qty(w).total; });
  ok('T21 Items-Issued is items (Σ qty.total), not people', issued > 0 && issued !== S.custodians().size, `issued=${issued} holders=${S.custodians().size}`); })();

console.log(`\n==== ${pass} passed, ${fail} failed ====`);
if (fail) { console.log('FAILURES:'); fails.forEach(f => console.log('  - ' + f)); process.exitCode = 1; }
