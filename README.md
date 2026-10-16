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

```bash
# FalkorDB (absolute paths are load-bearing — see ../prep.md)
/home/hatch/workspace/platform-sweeps/.venv/bin/python scripts/smoke_test.py
uvicorn app.main:app --port 8000
```

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

## Still to do (prep.md build order)

- Day 3 (Sat/Sun): deploy (FalkorDB Cloud or VPS), <3-min demo video
  (seed → "how do I get into Northline Foods?" → Ana → Raj → Leo → outreach
  draft), public repo, submit on WeMakeDevs before Sun Oct 18, 2:29 PM EDT
  (target ~noon).
- Optional: blog-post side entry (AirPods 5) after submitting.

AI assistance disclosure (event rule): this project was built with an AI
coding assistant; that will be stated in the submission.
