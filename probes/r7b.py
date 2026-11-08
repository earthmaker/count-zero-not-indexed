"""Part 1 R7b: three controls separating whether an ok/0 short-name answer is due to missing name resolution. Live calls to the public wheel swegemma 0.2.7.
  full    : re-query with the full dotted path of the graph node ending in ".symbol" (positive control: does an answer appear once the name is resolved?)
  gold    : neighbors query with the reference function's graph node name verbatim (exact-id positive control)
  title   : the issue's first line (title) passed as natural language to search_similar_code
Run: <venv>/bin/python r7b.py -> r7b.json
"""
import os
import json
from swegemma.tools import graph as tg
D = os.environ.get("G4P_DATA", "data")  # competition data dir (attached Kaggle dataset)
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(D + "/tasks.jsonl")}
syms = json.load(open("issue_symbols.json")); gold = json.load(open("gold_vs_graph.json"))
class Ctx:
    max_stdout_chars = 5000; graph_dir = D + "/graphs"; embeddings_dir = D + "/embeddings"
    def __init__(s, t): s.repo = t["repo"]; s.task = {"repo": t["repo"], "base_commit": t["base_commit"], "instance_id": t["instance_id"]}
    def check_budget(s, count_tool_call=True): return None
G = {}
def names(t):
    k = (t["repo"], t["base_commit"])
    if k not in G: G[k] = [n["name"] for n in json.load(open(f"{D}/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json"))["nodes"]]
    return G[k]
out = {"full": [], "gold": [], "title": []}
for r in syms:
    if r["kind"] != "suffix": continue
    t = tasks[r["id"]]; c = Ctx(t)
    cands = sorted(n for n in names(t) if n.endswith("." + r["sym"]))
    full = min(cands, key=len)
    nb = json.loads(tg.get_code_neighbors(c, full)); sim = json.loads(tg.search_similar_code(c, full, 5))
    out["full"].append(dict(id=r["id"], sym=r["sym"], full=full, ncand=len(cands), nb=(nb.get("status"), nb.get("count")), sim=(sim.get("status"), sim.get("count"))))
def mod(p):
    p = p[:-3]; p = p[4:] if p.startswith("src/") else p; p = p[:-9] if p.endswith("/__init__") else p
    return p.replace("/", ".")
seen = set()
for r in gold:
    if r["cat"] not in ("function", "class") or not r["hit"]: continue
    t = tasks[r["id"]]; n = mod(r["path"]) + "." + r["q"]
    if (r["id"], n) in seen: continue
    seen.add((r["id"], n)); c = Ctx(t)
    nb = json.loads(tg.get_code_neighbors(c, n))
    out["gold"].append(dict(id=r["id"], node=n, in_graph=n in set(names(t)), nb=(nb.get("status"), nb.get("count"))))
for i, t in tasks.items():
    title = t["problem_statement"].strip().splitlines()[0][:200]; c = Ctx(t)
    sim = json.loads(tg.search_similar_code(c, title, 5))
    out["title"].append(dict(id=i, title=title, sim=(sim.get("status"), sim.get("count"))))
json.dump(out, open("r7b.json", "w"), indent=0)
for k, v in out.items():
    key = "sim" if k == "title" else "nb"
    z = sum(1 for x in v if tuple(x[key]) == ("ok", 0)); bad = sum(1 for x in v if x[key][0] != "ok")
    print(f"{k:6s} n={len(v)}  ok/0 {z}  ok>0 {len(v)-z-bad}  non-ok {bad}")
f = out["full"]; print("full similar ok/0", sum(1 for x in f if tuple(x["sim"]) == ("ok", 0)), "/", len(f))
g = out["gold"]; print("gold node name matches graph name exactly", sum(x["in_graph"] for x in g), "/", len(g))
