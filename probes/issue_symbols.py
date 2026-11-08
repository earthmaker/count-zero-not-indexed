"""Part 1 (c): graph-tool answers when symbols from the issue text are passed verbatim. 129 tasks, live calls to the public wheel swegemma 0.2.7.

Symbols: identifier-like text in backticks, dotted `a.b` paths, `name(` call forms, CamelCase. Each symbol is matched against the graph as
  exact      : the string is a node name verbatim
  suffix     : some node ends in ".symbol" (would have resolved had the README's resolve_node_name existed)
  substring  : the symbol occurs inside some node name, ignoring case, but neither of the above
  absent     : nowhere in the graph (no partial name match either)
and the get_code_neighbors and search_similar_code answers (status, count) are recorded.
Run: <venv>/bin/python issue_symbols.py  -> issue_symbols.json
"""
import os
import json
import re
from collections import Counter

from swegemma.tools import graph as tg

D = os.environ.get("G4P_DATA", "data")  # competition data dir (attached Kaggle dataset)
tasks = [json.loads(l) for l in open(D + "/tasks.jsonl")]

IDENT = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"


def symbols(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"`([^`\n]{2,80})`", text):
        s = m.group(1).strip().rstrip("()")
        if re.fullmatch(IDENT, s):
            out.add(s)
    for m in re.finditer(r"\b(" + IDENT + r")\(", text):
        out.add(m.group(1))
    for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_.]*[A-Za-z0-9_])\b", text):
        out.add(m.group(1))
    for m in re.finditer(r"\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b", text):
        out.add(m.group(1))
    # drop very common words and Python builtins
    junk = {"print", "len", "str", "int", "dict", "list", "type", "isinstance", "range", "self", "True", "False", "None"}
    return {s for s in out if s not in junk and len(s) >= 3}


class Ctx:
    max_stdout_chars = 5000
    graph_dir = D + "/graphs"
    embeddings_dir = D + "/embeddings"

    def __init__(self, t):
        self.repo = t["repo"]
        self.task = {"repo": t["repo"], "base_commit": t["base_commit"], "instance_id": t["instance_id"]}

    def check_budget(self, count_tool_call=True):
        return None


rows = []
for t in tasks:
    g = json.load(open(f"{D}/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json"))
    names = [n["name"] for n in g["nodes"]]
    nset = set(names)
    c = Ctx(t)
    for s in sorted(symbols(t["problem_statement"])):
        if s in nset:
            kind = "exact"
        elif any(n.endswith("." + s) for n in names):
            kind = "suffix"
        elif any(s.lower() in n.lower() for n in names):
            kind = "substring"
        else:
            kind = "absent"
        nb = json.loads(tg.get_code_neighbors(c, s))
        sim = json.loads(tg.search_similar_code(c, s, 5))
        rows.append(dict(id=t["instance_id"], sym=s, kind=kind,
                         nb=(nb.get("status"), nb.get("count")), sim=(sim.get("status"), sim.get("count"))))

json.dump(rows, open("issue_symbols.json", "w"), indent=0)
print("tasks", len({r["id"] for r in rows}), "symbols", len(rows))
for k in ("exact", "suffix", "substring", "absent"):
    rs = [r for r in rows if r["kind"] == k]
    if not rs:
        continue
    nb0 = sum(1 for r in rs if r["nb"][0] == "ok" and not r["nb"][1])
    sim0 = sum(1 for r in rs if r["sim"][0] == "ok" and not r["sim"][1])
    err = sum(1 for r in rs if r["nb"][0] != "ok")
    print(f"{k:9s} {len(rs):5d}  neighbors ok/0 {nb0} ({nb0/len(rs):.0%})  similar ok/0 {sim0} ({sim0/len(rs):.0%})  non-ok {err}")
allz = sum(1 for r in rows if r["nb"] == ("ok", 0))
print(f"all neighbors ok/0 {allz}/{len(rows)} ({allz/len(rows):.0%})")
per = Counter()
for i in {r["id"] for r in rows}:
    rs = [r for r in rows if r["id"] == i]
    per["all symbols ok/0" if all(r["nb"] == ("ok", 0) for r in rs) else "at least one answer"] += 1
print("task-level neighbors:", dict(per))
