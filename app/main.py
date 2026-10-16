"""WarmPath API — Graph Hacks: Context for AI Agents, Track 01.

Run: uvicorn app.main:app --port 8000  (with FalkorDB on 127.0.0.1:6379)
"""
import csv
import io
import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .graph import (
    add_note,
    add_signal,
    call_list,
    get_graph,
    get_notes,
    get_signals,
    ingest_rows,
    intro_paths,
    outreach_draft,
    seed,
    seed_signals,
    warm_accounts,
)

app = FastAPI(title="WarmPath")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class NoteIn(BaseModel):
    person: str
    text: str


class SignalIn(BaseModel):
    kind: str
    text: str
    date: str


class OutreachIn(BaseModel):
    target: str


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    g = get_graph()
    g.query("RETURN 1")
    return {"status": "ok", "graph_db": "FalkorDB"}


@app.post("/seed")
def do_seed():
    result = seed(get_graph())
    result.update(seed_signals(get_graph()))
    return result


@app.get("/intro-path")
def intro_path(target: str):
    paths = intro_paths(get_graph(), target)
    return {"target": target, "paths": paths, "best": paths[0] if paths else None}


@app.get("/warm-accounts")
def warm():
    return {"warm_accounts": warm_accounts(get_graph())}


@app.post("/notes")
def note(body: NoteIn):
    add_note(get_graph(), body.person, body.text)
    return {"saved": True}


@app.get("/notes")
def notes(person: str):
    return {"person": person, "notes": get_notes(get_graph(), person)}


# --- Day 2 (2026-10-16) -----------------------------------------------------


@app.post("/ingest")
async def ingest(req: Request):
    """Body: raw CSV text, header name,company,role,knows
    (knows = semicolon-separated names already in the graph)."""
    text = (await req.body()).decode("utf-8")
    rows = []
    for raw in csv.DictReader(io.StringIO(text)):
        rows.append({
            "name": raw.get("name", ""),
            "company": raw.get("company", ""),
            "role": raw.get("role", ""),
            "knows": raw.get("knows", ""),
        })
    return ingest_rows(get_graph(), rows)


@app.post("/enrich/{company}")
def enrich(company: str, body: SignalIn):
    return add_signal(get_graph(), company, body.kind, body.text, body.date)


@app.get("/signals")
def signals(company: str):
    return {"company": company, "signals": get_signals(get_graph(), company)}


@app.get("/call-list")
def ranked_call_list():
    return {"call_list": call_list(get_graph())}


@app.post("/outreach")
def outreach(body: OutreachIn):
    return outreach_draft(get_graph(), body.target)
