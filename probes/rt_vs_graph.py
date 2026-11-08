"""Part 1 (b): share of runtime edges (between library functions) present in the competition graph, by category; and edges into reference-edit functions."""
import json, glob, os, re, collections
# Work folder: part/tasks.jsonl, full/graphs, rt_out/ (output of rt_batch.py), gold_vs_graph.json; kept outside this release
S = os.environ["G4"]
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(S + "/part/tasks.jsonl")}
gold = collections.defaultdict(set)
for r in json.load(open(S + "/gold_vs_graph.json")):
    if r["cat"] in ("function", "async", "nested", "class"): gold[r["id"]].add((r["path"], r["q"]))
def modname(path):
    p = path[:-3]
    if p.startswith("src/"): p = p[4:]
    if p.endswith("/__init__"): p = p[:-9]
    return p.replace("/", ".")
def is_lib(path):
    return path.endswith(".py") and not re.search(r"(^|/)(tests?|testing|docs_src|docs|scripts)/|(^|/)(test_[^/]*|conftest|_swegemma_stubs)\.py$", path)
E = collections.Counter(); cat = collections.Counter(); G = collections.Counter(); per_task = {}
for iid, t in tasks.items():
    f = f"{S}/rt_out/{iid}.json"
    if not os.path.exists(f): continue
    d = json.load(open(f))
    node_meta = {(n["path"], n["qualname"], n["lineno"]): n for n in d["nodes"]}
    g = json.load(open(glob.glob(f"{S}/full/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json")[0]))
    gn = {n["name"] for n in g["nodes"]}; ge = {(e["source"], e["target"]) for e in g["edges"]}
    tg = {"in": 0, "in_graph": 0}
    for e in d["edges"]:
        (cp, cq, cl), (dp, dq, dl) = e["caller"], e["callee"]
        if not (is_lib(cp) and is_lib(dp)) or "<module>" in (cq, dq): continue
        cm = node_meta.get((dp, dq, dl), {})
        if cm.get("is_lambda_or_comp") or "<lambda>" in dq or "<genexpr>" in dq or "comp>" in dq: continue
        cn, dn = modname(cp) + "." + cq, modname(dp) + "." + dq
        hit = (cn, dn) in ge
        if "<locals>" in dq or "<locals>" in cq: k = "nested"
        elif cm.get("is_async") or node_meta.get((cp, cq, cl), {}).get("is_async"): k = "async"
        elif not e["name_on_line"]: k = "name_not_on_line"
        elif cm.get("n_decorators"): k = "decorated"
        else: k = "plain"
        E[(k, hit)] += 1
        if not hit:
            cat[(k, "endpoints_in_graph" if (cn in gn and dn in gn) else "endpoint_missing")] += 1
        if (dp, dq) in gold[iid] or (dp, dq.split(".<locals>")[0]) in gold[iid]:
            tg["in"] += 1; tg["in_graph"] += hit
    if gold[iid]: per_task[iid] = tg
tot = sum(E.values()); h = sum(v for (k, hit), v in E.items() if hit)
print(f"library-internal runtime edges {tot} | in graph {h} ({h/tot:.1%})")
for k in ("plain", "decorated", "name_not_on_line", "async", "nested"):
    a, b = E[(k, True)], E[(k, False)]
    print(f"  {k:18s} present {a:5d} missing {b:5d}  recall {a/(a+b) if a+b else 0:.1%}")
print("cause layer of missing edges:", dict(cat))
w = [v for v in per_task.values() if v["in"]]
print(f"tasks with a runtime edge into a reference function {len(w)} / tasks with a reference {len(per_task)}")
print(f"  of those, at least one edge in graph {sum(1 for v in w if v['in_graph'])} | none in graph {sum(1 for v in w if not v['in_graph'])}")
print(f"  edge level {sum(v['in_graph'] for v in w)}/{sum(v['in'] for v in w)}")
json.dump(per_task, open(S + "/rt_gold_edges.json", "w"), indent=1)
