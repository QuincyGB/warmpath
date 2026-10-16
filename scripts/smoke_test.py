"""Day-1 smoke test: seed -> intro path -> warm accounts -> memory round-trip.
Run with the durable venv python, FalkorDB listening on 127.0.0.1:6379.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("WARMPATH_GRAPH", "warmpath_smoke")

from app.graph import add_note, get_graph, get_notes, intro_paths, seed, warm_accounts

g = get_graph()
print("seed:", seed(g))

paths = intro_paths(g, "Leo Marsh")
print("intro paths to Leo Marsh:", paths)
assert paths and paths[0][0] == "Quincy" and paths[0][-1] == "Leo Marsh", paths
assert len(paths[0]) == 3, f"expected 2-hop best path via Kim Osei, got {paths[0]}"

warm = warm_accounts(g)
print("warm accounts:", warm)
assert "Northline Foods" in warm and "Acme Logistics" in warm, warm

add_note(g, "Leo Marsh", "Budget review in November; prefers email intros.")
notes = get_notes(g, "Leo Marsh")
print("notes:", notes)
assert notes and "November" in notes[0]

print("SMOKE PASS")

# --- Day-2 additions (2026-10-16): ingest -> enrich -> call list -> outreach
import csv
import io

from app.graph import call_list, get_signals, ingest_rows, outreach_draft, add_signal, seed_signals

seed_signals(g)

CSV_TEXT = """name,company,role,knows
Dana Lee,BrightMart,VP Operations,Quincy
Sam Ortiz,BrightMart,Procurement Lead,Dana Lee
Ana Torres,Acme Logistics,Ops Manager,Sam Ortiz
"""
rows = list(csv.DictReader(io.StringIO(CSV_TEXT)))
print("ingest:", ingest_rows(g, rows))
print("ingest again (idempotent):", ingest_rows(g, rows))

add_signal(g, "BrightMart", "hiring",
           "BrightMart is hiring a warehouse automation lead (posted Oct 15).",
           "2026-10-15")
sigs = get_signals(g, "BrightMart")
print("BrightMart signals:", sigs)
assert sigs and sigs[0]["kind"] == "hiring", sigs

cl = call_list(g)
print("call list:", [(r["company"], r["hops"], r["path"]) for r in cl])
bright = [r for r in cl if r["company"] == "BrightMart"]
assert bright, cl
assert bright[0]["path"][0] == "Quincy" and bright[0]["contact"]["name"] in (
    "Dana Lee", "Sam Ortiz"), bright
assert bright[0]["why_now"] and "warehouse automation" in bright[0]["why_now"]["text"], bright
north = [r for r in cl if r["company"] == "Northline Foods"]
assert north and north[0]["why_now"]["source"] == "demo-seed", north

out = outreach_draft(g, "Sam Ortiz")
print("outreach to Sam Ortiz:", out)
assert out["draft"] and "Dana" in out["draft"], out
assert "warehouse automation" in out["draft"], out

print("DAY2 SMOKE PASS")
