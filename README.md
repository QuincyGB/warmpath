# WarmPath — graph-powered sales intelligence

Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB), Track 01 —
Agents That Act on Connected Data. Build window: Oct 15–18, 2026 IST
(Toronto: Wed Oct 14, 2:31 PM EDT → Sun Oct 18, 2:29 PM EDT).

**One-liner:** an agent that builds a living relationship graph of your market
in FalkorDB and answers the question every rep asks: *"who do I know that can
intro me to X?"* — and shows the exact path behind every answer.

## Day-1 state (2026-10-14 evening)

- FalkorDB running locally (native rootfs workaround, see `../prep.md`) —
  found DOWN again at 19:37 EDT, restarted with the absolute-path command,
  CREATE/read/DELETE verified.
- Graph layer (`app/graph.py`): seed demo network, intro-path traversal
  (multi-hop `KNOWS`), warm-account discovery (≤2 hops), session memory
  (`NOTED` notes persisted as graph nodes).
- API (`app/main.py`): `/health`, `/seed`, `/intro-path`, `/warm-accounts`,
  `/notes`.
- Smoke test passes end-to-end: `scripts/smoke_test.py`.

## Run

FalkorDB is the primary store and the product's core — every feature below
is a graph query against it. Start it first (or point `FALKORDB_HOST` /
`FALKORDB_PORT` at any FalkorDB instance):

```bash
docker run -p 6379:6379 falkordb/falkordb   # FalkorDB on 127.0.0.1:6379
pip install -r requirements.txt
python scripts/smoke_test.py                # end-to-end: seed -> paths -> call list -> draft
uvicorn app.main:app --port 8000            # UI at http://127.0.0.1:8000
```

Demo flow (also the demo video): click **Seed demo network**, read the
ranked call list (warm accounts with the path and "why now" behind each),
then draft an intro request for **Leo Marsh** and watch it cite the path
Quincy → Kim Osei → Leo Marsh.

## Day-2 state (2026-10-16, built + verified by Ren)

- CSV paste ingest: `POST /ingest` (raw CSV text, header
  `name,company,role,knows`), idempotent MERGE; ingested KNOWS edges are
  written both ways (a pasted contact relationship is mutual, which is what
  makes the new network traversable from Quincy).
- Research enrichment: `POST /enrich/{company}` + `GET /signals` — Signal
  nodes (hiring/news/funding, text, date, source) on companies. Seed carries
  4 demo signals labelled `demo-seed` and shown as "demo data" in the UI.
- Ranked call list: `GET /call-list` — warm companies ranked by shortest
  intro path, then freshest signal; each row shows contact, the full path,
  the "why now" signal, and session notes on people along the path.
- Outreach draft generator: `POST /outreach` — deterministic template draft
  asking the first hop for the intro, citing path + why-now + notes; works
  fully offline.
- Minimal UI at `/`: seed button, CSV paste box, call-list table, draft box.
- Smoke test extended (`scripts/smoke_test.py`): ingest → enrich →
  call-list ranking → outreach draft all asserted — DAY2 SMOKE PASS, plus a
  live uvicorn pass over every endpoint on 2026-10-16.
- FalkorDB was found DOWN again on 2026-10-16 and restarted with the
  absolute-path command in `../prep.md`; it does not survive restarts.

## Submission state (Sun Oct 18, 2026)

- Demo video recorded from the real running app (seed → ranked call list →
  intro path to Leo Marsh → outreach draft), ~2 minutes, narrated.
- Deployment: the FalkorDB connection is fully env-configurable
  (`FALKORDB_URL`, or `FALKORDB_HOST` / `FALKORDB_PORT` /
  `FALKORDB_USERNAME` / `FALKORDB_PASSWORD` / `FALKORDB_SSL`; defaults are
  local 127.0.0.1:6379, so local runs are unchanged). A Render blueprint
  (`render.yaml`) deploys the API against a FalkorDB Cloud instance —
  set the `FALKORDB_*` values from the Cloud instance in the Render
  dashboard and the same code runs hosted or local.
- Optional: blog-post side entry (AirPods 5) after submitting.

AI assistance disclosure (event rule): this project was built with an AI
coding assistant; that will be stated in the submission.
