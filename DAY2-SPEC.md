# WarmPath — Day-2 build spec (Fri Oct 16, 2026)

Written Thu Oct 15 night so Friday's session starts cold with no planning
overhead. Order follows prep.md's build order. Day-1 base is verified:
FalkorDB was found DOWN again Thu ~20:36 EDT, restarted with the
absolute-path command in prep.md, and `scripts/smoke_test.py` passes
end-to-end (seed 6 people / 3 companies, intro paths to Leo Marsh,
warm accounts, notes round-trip — SMOKE PASS).

Existing surface (do not rebuild): `app/graph.py` — `seed()`,
`intro_paths()`, `warm_accounts()`, `add_note()`, `get_notes()`;
`app/main.py` — `/health`, `/seed`, `/intro-path`, `/warm-accounts`,
`/notes` (POST+GET).

## 1. CSV paste ingest
- `POST /ingest` — body: raw CSV text with header
  `name,company,role,knows` (`knows` = semicolon-separated names already
  in the graph). Creates/merges Person + Company nodes, WORKS_AT and
  KNOWS edges. Idempotent (MERGE on name).
- Graph fn: `ingest_rows(g, rows)` in `app/graph.py`.
- Minimal UI: one static page (`app/static/index.html`) with a paste
  box + Ingest button; served by FastAPI StaticFiles. No framework.

## 2. Research enrichment (signals → nodes)
- `POST /enrich/{company}` — attaches Signal nodes (kind: hiring /
  news / funding; text; date) with a SIGNAL edge to the Company.
- Source for the demo: hand-seeded signals for the 3 seed companies are
  acceptable IF labelled as demo data in the UI; live fetch (news API)
  only if time remains after items 1, 3, 4 pass smoke.
- Graph fn: `add_signal(g, company, kind, text, date)`.

## 3. Ranked call list with "why now" briefs
- `GET /call-list` — warm accounts ranked by: shortest intro-path
  length, then most recent Signal date. Each row: company, best path
  (from `intro_paths`), latest signal text as the "why now" line,
  any NOTED notes on people along the path.
- This is the demo's money view — the Sun demo script
  (seed → "how do I get into Northline Foods?" → Ana → Raj → Leo →
  outreach draft) reads from this endpoint.

## 4. Outreach draft generator
- `POST /outreach` — body: target person + path. Returns a short draft
  asking the first hop for the intro, referencing the "why now" signal
  and any session note. Template-first (deterministic); LLM polish is
  optional and must not block the endpoint working offline.

## Acceptance for Friday
- Smoke test extended: ingest a 3-row CSV → enrich one company →
  `/call-list` returns it ranked with a why-now line → `/outreach`
  returns a draft naming the first hop. All offline, no external keys.
- Then stop: deploy + repo + video are Saturday/Sunday per the weekend
  run-sheet (~/workspace/hackathons/weekend-20261017-18-run-sheet.md).

## Not Friday's problem
- AMD/FieldBrain: gated on the AMD credits approval clock (2–3 business
  days from the Member Perks request can land after the Sun 11 AM EDT
  close). Friday stays WarmPath-only, per the run-sheet.
- Public GitHub repos for both entries: still local-only as of Thu
  night (FieldBrain has git, no remote; WarmPath is not yet a git
  repo). Publishing needs Quincy's yes — carried as a separate decision,
  needed before either filing.
