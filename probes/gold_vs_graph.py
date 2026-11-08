"""129 tasks: is each reference-edit function (gold_targets) a graph node? Counts by category. Only the .py files touched by the patch are extracted from the snapshot."""
import json, os, sys, tarfile, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gold_targets import targets, changed_old_lines
# Work folder: part/tasks.jsonl, full/ (all competition data). Competition data may not be redistributed, so it stays outside this release
S = os.environ["G4"]; F = S + "/full"
tasks = [json.loads(l) for l in open(S + "/part/tasks.jsonl")]
def modname(path):
    p = path[:-3]
    if p.startswith("src/"): p = p[4:]
    if p.endswith("/__init__"): p = p[:-9]
    return p.replace("/", ".")
rows = []
for t in tasks:
    snap = f"{F}/snapshots/{t['instance_id']}.tgz"
    if not os.path.exists(snap): continue
    root = f"{S}/src/{t['instance_id']}"
    want = ["./" + p for p in changed_old_lines(t["patch"])]
    os.makedirs(root, exist_ok=True)
    with tarfile.open(snap) as tf:
        names = set(tf.getnames())
        tf.extractall(root, members=[tf.getmember(w) for w in want if w in names])
    g = json.load(open(f"{F}/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json"))
    nodes = {n["name"] for n in g["nodes"]}
    for x in targets(root, t["patch"]):
        if x["kind"] in ("module", "new_file"): cat = x["kind"]; hit = None
        else:
            q = x["qualname"]
            name = modname(x["path"]) + "." + q
            hit = name in nodes
            cat = "nested" if "<locals>" in q else ("async" if x.get("is_async") else x["kind"])
        rows.append(dict(id=t["instance_id"], repo=t["repo"], path=x["path"], q=x["qualname"], cat=cat, hit=hit))
json.dump(rows, open(S + "/gold_vs_graph.json", "w"), ensure_ascii=False, indent=1)
ids = {r["id"] for r in rows}
c = collections.Counter((r["cat"], r["hit"]) for r in rows)
print("tasks", len(ids), "gold units", len(rows))
for k, v in sorted(c.items(), key=str): print(k, v)
# Task level: is at least one function-level gold target in the graph?
by = collections.defaultdict(list)
for r in rows:
    if r["hit"] is not None: by[r["id"]].append(r["hit"])
print("tasks with function gold", len(by), "| none in graph", sum(1 for v in by.values() if not any(v)), "| at least one in graph", sum(1 for v in by.values() if any(v)))
