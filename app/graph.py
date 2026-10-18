"""WarmPath graph layer — FalkorDB is the primary store and the product's core.

All reasoning (intro paths, warm accounts, session memory) is a graph query.
No LLM is involved in these paths; results are explainable because every
answer returns the actual traversal that produced it.
"""
import os

from falkordb import FalkorDB

GRAPH_NAME = os.environ.get("WARMPATH_GRAPH", "warmpath")


def _connect():
    """FalkorDB connection, fully env-configurable (defaults = local dev).

    Precedence:
      1. FALKORDB_URL — full connection URL, e.g.
         redis://user:password@host:port  (rediss:// for TLS).
         This is the format FalkorDB Cloud hands out.
      2. Discrete vars: FALKORDB_HOST (default 127.0.0.1),
         FALKORDB_PORT (default 6379), FALKORDB_USERNAME,
         FALKORDB_PASSWORD, FALKORDB_SSL=1 for TLS without a URL.
    """
    url = os.environ.get("FALKORDB_URL")
    if url:
        return FalkorDB.from_url(url)
    kwargs = {
        "host": os.environ.get("FALKORDB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FALKORDB_PORT", "6379")),
    }
    if os.environ.get("FALKORDB_USERNAME"):
        kwargs["username"] = os.environ["FALKORDB_USERNAME"]
    if os.environ.get("FALKORDB_PASSWORD"):
        kwargs["password"] = os.environ["FALKORDB_PASSWORD"]
    if os.environ.get("FALKORDB_SSL", "").lower() in ("1", "true", "yes"):
        kwargs["ssl"] = True
    return FalkorDB(**kwargs)


def get_graph():
    return _connect().select_graph(GRAPH_NAME)


SEED_PEOPLE = [
    # name, title, company
    ("Quincy", "Sales Rep (you)", None),
    ("Ana Torres", "Ops Manager", "Acme Logistics"),
    ("Raj Patel", "VP Sales", "Northline Foods"),
    ("Kim Osei", "Consultant", "Acme Logistics"),
    ("Leo Marsh", "CFO", "Northline Foods"),
    ("Priya Nair", "Head of Procurement", "Northline Foods"),
]
SEED_COMPANIES = ["Acme Logistics", "Northline Foods", "ColdChain Co"]
# KNOWS edges: (from, to)
SEED_KNOWS = [
    ("Quincy", "Ana Torres"),
    ("Quincy", "Kim Osei"),
    ("Ana Torres", "Raj Patel"),
    ("Kim Osei", "Leo Marsh"),
    ("Raj Patel", "Leo Marsh"),
    ("Raj Patel", "Priya Nair"),
]


def seed(g=None):
    """Reset and seed the demo network from prep.md (single demo scenario)."""
    g = g or get_graph()
    g.query("MATCH (n) DETACH DELETE n")
    for name, title, _ in SEED_PEOPLE:
        g.query(
            "CREATE (p:Person {name: $name, title: $title})",
            {"name": name, "title": title},
        )
    for company in SEED_COMPANIES:
        g.query("CREATE (c:Company {name: $name})", {"name": company})
    for name, _, company in SEED_PEOPLE:
        if company:
            g.query(
                "MATCH (p:Person {name: $p}), (c:Company {name: $c}) "
                "CREATE (p)-[:WORKS_AT]->(c)",
                {"p": name, "c": company},
            )
    for a, b in SEED_KNOWS:
        g.query(
            "MATCH (a:Person {name: $a}), (b:Person {name: $b}) "
            "CREATE (a)-[:KNOWS]->(b)",
            {"a": a, "b": b},
        )
    return {"people": len(SEED_PEOPLE), "companies": len(SEED_COMPANIES),
            "knows_edges": len(SEED_KNOWS)}


def intro_paths(g, target_name, max_hops=4):
    """All intro paths from Quincy to a target person, shortest first.

    Explainability: returns the ordered names along each path so the UI can
    literally show 'Quincy -> Ana Torres -> Raj Patel -> Leo Marsh'.
    """
    res = g.query(
        "MATCH p = (me:Person {name: 'Quincy'})-[:KNOWS*1..%d]->"
        "(t:Person {name: $target}) RETURN p" % max_hops,
        {"target": target_name},
    )
    paths = []
    for row in res.result_set:
        path = row[0]
        names = [n.properties.get("name") for n in path.nodes()]
        paths.append(names)
    paths.sort(key=len)
    return paths


def warm_accounts(g, max_hops=2):
    """Companies reachable within max_hops KNOWS edges of Quincy."""
    res = g.query(
        "MATCH (me:Person {name: 'Quincy'})-[:KNOWS*1..%d]->(p:Person)"
        "-[:WORKS_AT]->(c:Company) RETURN DISTINCT c.name" % max_hops
    )
    return sorted(row[0] for row in res.result_set)


def add_note(g, person_name, note):
    """Session memory: persist a note about a person as a graph node."""
    g.query(
        "MATCH (p:Person {name: $p}) CREATE (n:Note {text: $text}) "
        "CREATE (p)-[:NOTED]->(n)",
        {"p": person_name, "text": note},
    )


def get_notes(g, person_name):
    res = g.query(
        "MATCH (p:Person {name: $p})-[:NOTED]->(n:Note) RETURN n.text",
        {"p": person_name},
    )
    return [row[0] for row in res.result_set]


# ---------------------------------------------------------------------------
# Day 2 (2026-10-16): ingest, enrichment signals, ranked call list, outreach.
# All reasoning stays in graph queries; drafts are deterministic templates so
# the whole flow works offline with no external keys.
# ---------------------------------------------------------------------------

SEED_SIGNALS = [
    # company, kind, text, date — demo data, labelled as such in the UI
    ("Northline Foods", "hiring",
     "Northline Foods is hiring a Director of Supply Chain (posted Oct 12) — a new budget owner is arriving.",
     "2026-10-12"),
    ("Northline Foods", "news",
     "Northline Foods won a regional grocery distribution contract and is expanding to 40 new stores.",
     "2026-10-09"),
    ("Acme Logistics", "news",
     "Acme Logistics announced a new cold-storage warehouse opening in November.",
     "2026-10-08"),
    ("ColdChain Co", "funding",
     "ColdChain Co raised a seed round to expand refrigerated last-mile delivery.",
     "2026-10-05"),
]


def add_signal(g, company, kind, text, date, source="manual"):
    """Research enrichment: attach a Signal node to a Company."""
    g.query(
        "MERGE (c:Company {name: $c}) "
        "CREATE (s:Signal {kind: $kind, text: $text, date: $date, source: $source}) "
        "CREATE (c)-[:HAS_SIGNAL]->(s)",
        {"c": company, "kind": kind, "text": text, "date": date, "source": source},
    )
    return {"company": company, "kind": kind, "date": date}


def get_signals(g, company):
    res = g.query(
        "MATCH (c:Company {name: $c})-[:HAS_SIGNAL]->(s:Signal) "
        "RETURN s.kind, s.text, s.date, s.source",
        {"c": company},
    )
    out = [
        {"kind": r[0], "text": r[1], "date": r[2], "source": r[3]}
        for r in res.result_set
    ]
    out.sort(key=lambda s: s["date"] or "", reverse=True)
    return out


def seed_signals(g):
    for company, kind, text, date in SEED_SIGNALS:
        add_signal(g, company, kind, text, date, source="demo-seed")
    return {"signals": len(SEED_SIGNALS)}


def ingest_rows(g, rows):
    """CSV ingest: rows of {name, company, role, knows:[names]}.

    Idempotent (MERGE on name). KNOWS from a pasted contact list is a mutual
    relationship, so edges are written both ways — that is what makes the
    ingested network traversable by intro_paths from Quincy.
    """
    people, companies, edges = 0, 0, 0
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        role = (row.get("role") or "").strip()
        g.query(
            "MERGE (p:Person {name: $name}) SET p.title = "
            "CASE WHEN $role <> '' THEN $role ELSE p.title END",
            {"name": name, "role": role},
        )
        people += 1
        company = (row.get("company") or "").strip()
        if company:
            g.query(
                "MATCH (p:Person {name: $p}) MERGE (c:Company {name: $c}) "
                "MERGE (p)-[:WORKS_AT]->(c)",
                {"p": name, "c": company},
            )
            companies += 1
        knows = row.get("knows") or []
        if isinstance(knows, str):
            knows = [k.strip() for k in knows.split(";") if k.strip()]
        for other in knows:
            g.query(
                "MERGE (o:Person {name: $o}) "
                "WITH o MATCH (p:Person {name: $p}) "
                "MERGE (p)-[:KNOWS]->(o) MERGE (o)-[:KNOWS]->(p)",
                {"p": name, "o": other},
            )
            edges += 1
    return {"people": people, "companies": companies, "knows_edges": edges}


def _company_people(g, company):
    res = g.query(
        "MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: $c}) "
        "RETURN p.name, p.title",
        {"c": company},
    )
    return [{"name": r[0], "title": r[1]} for r in res.result_set]


def call_list(g):
    """Ranked call list: warm companies by shortest intro path, then freshest
    signal. Each row carries its best path, the 'why now' latest signal, and
    any session notes on people along the path."""
    res = g.query("MATCH (c:Company) RETURN c.name")
    rows = []
    for (company,) in res.result_set:
        best_path, contact = None, None
        for person in _company_people(g, company):
            for path in intro_paths(g, person["name"]):
                if best_path is None or len(path) < len(best_path):
                    best_path, contact = path, person
        if best_path is None:
            continue  # not warm — no intro path from Quincy
        signals = get_signals(g, company)
        notes = []
        for name in best_path:
            for note in get_notes(g, name):
                notes.append({"person": name, "text": note})
        rows.append({
            "company": company,
            "contact": contact,
            "path": best_path,
            "hops": len(best_path) - 1,
            "why_now": signals[0] if signals else None,
            "notes_on_path": notes,
        })
    rows.sort(key=lambda r: (
        r["hops"],
        -(int((r["why_now"] or {}).get("date", "0000-00-00").replace("-", ""))),
    ))
    return rows


def outreach_draft(g, target_name):
    """Deterministic outreach draft asking the first hop for the intro.
    Returns {draft: None, reason} when no intro path exists."""
    paths = intro_paths(g, target_name)
    if not paths:
        return {"target": target_name, "draft": None,
                "reason": "No intro path from Quincy to this person in the graph."}
    path = paths[0]
    res = g.query(
        "MATCH (p:Person {name: $p}) OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company) "
        "RETURN p.title, c.name",
        {"p": target_name},
    )
    title, company = (res.result_set[0] if res.result_set else (None, None))
    signals = get_signals(g, company) if company else []
    why = signals[0] if signals else None
    target_notes = get_notes(g, target_name)

    who = target_name
    if title or company:
        who += " (" + ", ".join(x for x in [title, company] if x) + ")"
    _t = why["text"] if why else ""
    why_clause = f" {_t if _t.endswith('.') else _t + '.'}" if why else ""
    note_clause = f" I noted: {target_notes[0]}" if target_notes else ""

    if len(path) > 2:
        first_hop = path[1]
        draft = (
            f"Hi {first_hop.split()[0]} — quick favour. I'm trying to reach {who}, "
            f"and you're the warmest path I have ({' → '.join(path)})."
            f"{why_clause} Would you be open to a short intro? Happy to send a "
            f"forwardable blurb so it's zero work on your end.{note_clause} "
            f"Thanks! — Quincy"
        )
    else:
        draft = (
            f"Hi {target_name.split()[0]} — reaching out directly since we already "
            f"know each other.{why_clause} Open to a short call next week to compare "
            f"notes?{note_clause} — Quincy"
        )
    return {"target": target_name, "path": path, "why_now": why, "draft": draft}
