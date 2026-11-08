"""Part 1 final statistics: restricts to judgeable tasks, with Wilson 95% intervals, (repository, commit) deduplication, per-repository strata, task-cluster bootstrap and the R7 composite.
Inputs: gold_vs_graph.json, rt_out/, rt_out_gold/, issue_symbols.json, gold_check.json, full/graphs/
"""
import collections, glob, json, math, os, random, re
S = os.environ["G4"]   # work folder (part/, full/, rt_out/, rt_out_gold/)
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(S + "/part/tasks.jsonl")}
gc = {r["id"]: r for r in json.load(open(S + "/gold_check.json"))}
STRICT = {i for i, r in gc.items() if r["verdict"] == "judgeable"}
RELAX = STRICT | {i for i, r in gc.items() if r.get("relaxed")}

def wilson(k, n, z=1.96):
    if not n: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)
def fmt(k, n):
    lo, hi = wilson(k, n); return f"{k}/{n} ({k/n:.1%}, 95% CI {lo:.1%}–{hi:.1%})" if n else f"{k}/0"
def boot(pairs, B=2000, seed=0):
    """pairs: per task (present, total). Cluster bootstrap resampling tasks; 2.5 and 97.5 percentiles."""
    rnd = random.Random(seed); v = []
    for _ in range(B):
        s = [pairs[rnd.randrange(len(pairs))] for _ in pairs]; a = sum(x for x, _ in s); b = sum(y for _, y in s)
        v.append(a / b if b else 0)
    v.sort(); return v[int(.025 * B)], v[int(.975 * B)]

gold_rows = json.load(open(S + "/gold_vs_graph.json"))
gold = collections.defaultdict(set)
for r in gold_rows:
    if r["cat"] in ("function", "async", "nested", "class"): gold[r["id"]].add((r["path"], r["q"]))
def modname(p):
    p = p[:-3]; p = p[4:] if p.startswith("src/") else p; p = p[:-9] if p.endswith("/__init__") else p
    return p.replace("/", ".")
def is_lib(p):
    return p.endswith(".py") and not re.search(r"(^|/)(tests?|testing|docs_src|docs|scripts)/|(^|/)(test_[^/]*|conftest|_swegemma_stubs)\.py$", p)
GC = {}
def graph(t):
    k = (t["repo"], t["base_commit"])
    if k not in GC:
        g = json.load(open(glob.glob(f"{S}/full/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json")[0]))
        GC[k] = ({n["name"] for n in g["nodes"]}, {(e["source"], e["target"]) for e in g["edges"]})
    return GC[k]
def edges(iid, d_):
    """Library-internal runtime edges of one task -> [(category, in graph, into reference, (caller, callee))]"""
    f = f"{S}/{d_}/{iid}.json"
    if not os.path.exists(f): return None
    d = json.load(open(f)); t = tasks[iid]; gn, ge = graph(t)
    meta = {(n["path"], n["qualname"], n["lineno"]): n for n in d["nodes"]}; out = []
    for e in d["edges"]:
        (cp, cq, cl), (dp, dq, dl) = e["caller"], e["callee"]
        if not (is_lib(cp) and is_lib(dp)) or "<module>" in (cq, dq): continue
        cm = meta.get((dp, dq, dl), {})
        if cm.get("is_lambda_or_comp") or "<lambda>" in dq or "<genexpr>" in dq or "comp>" in dq: continue
        cn, dn = modname(cp) + "." + cq, modname(dp) + "." + dq
        if "<locals>" in dq or "<locals>" in cq: k = "nested"
        elif cm.get("is_async") or meta.get((cp, cq, cl), {}).get("is_async"): k = "async"
        elif not e["name_on_line"]: k = "name_not_on_line"
        elif cm.get("n_decorators"): k = "decorated"
        else: k = "plain"
        ing = (dp, dq) in gold[iid] or (dp, dq.split(".<locals>")[0]) in gold[iid]
        out.append((k, (cn, dn) in ge, ing, (cn, dn)))
    return out

sym = collections.defaultdict(list)
for r in json.load(open(S + "/issue_symbols.json")): sym[r["id"]].append(r)

def report(name, ids):
    ids = sorted(ids); print(f"\n== {name} - tasks {len(ids)}")
    commits = {(tasks[i]["repo"], tasks[i]["base_commit"]) for i in ids}
    print(f"  (repository, commit) unique {len(commits)} | per repository {dict(collections.Counter(tasks[i]['repo'].split('/')[1] for i in ids))}")
    # (a) reference units: same commit and same unit counted once
    seen = set(); C = collections.Counter()
    for r in gold_rows:
        if r["id"] not in ids or r["cat"] not in ("function", "async", "nested", "class"): continue
        key = (r["repo"], tasks[r["id"]]["base_commit"], r["path"], r["q"])
        if key in seen: continue
        seen.add(key); C[(r["cat"], bool(r["hit"]))] += 1
    print("  (a) reference unit is a graph node (commit/unit deduplicated):")
    for c in ("function", "class", "async", "nested"):
        print(f"     {c:9s} {fmt(C[(c, True)], C[(c, True)] + C[(c, False)])}")
    fz = [i for i in ids if gold[i]]
    none = [i for i in fz if not any(r["hit"] for r in gold_rows if r["id"] == i and r["cat"] in ("function", "async", "nested", "class"))]
    print(f"     tasks where no reference function is present {fmt(len(none), len(fz))}")
    # (b) edges: base traces, by category, task-cluster bootstrap
    for d_ in ("rt_out", "rt_out_gold"):
        per = {i: edges(i, d_) for i in ids}; per = {i: v for i, v in per.items() if v}
        allE = [x for v in per.values() for x in v]; h = sum(x[1] for x in allE)
        lo, hi = boot([(sum(x[1] for x in v), len(v)) for v in per.values() if v])
        print(f"  (b) [{d_}] edge files {len(per)} | library-internal {len(allE)} | in graph {h} ({h/len(allE):.1%}, task-cluster bootstrap {lo:.1%}-{hi:.1%})")
        for k in ("plain", "decorated", "name_not_on_line", "async", "nested"):
            a = sum(1 for x in allE if x[0] == k and x[1]); n = sum(1 for x in allE if x[0] == k)
            pr = [(sum(1 for x in v if x[0] == k and x[1]), sum(1 for x in v if x[0] == k)) for v in per.values()]
            pr = [p for p in pr if p[1]]
            b = boot(pr) if pr else (0, 0)
            print(f"       {k:17s} {a:5d}/{n:5d} {a/n if n else 0:6.1%}  [{b[0]:.1%}–{b[1]:.1%}]")
        for repo in sorted({tasks[i]['repo'] for i in per}):
            v = [x for i, e in per.items() if tasks[i]["repo"] == repo for x in e]
            if v: print(f"       repository {repo.split('/')[1]:9s} {sum(x[1] for x in v)}/{len(v)} {sum(x[1] for x in v)/len(v):.1%}")
        w = {i: [x for x in v if x[2]] for i, v in per.items() if gold[i]}
        w = {i: v for i, v in w.items() if v}
        z = [i for i, v in w.items() if not any(x[1] for x in v)]
        print(f"       tasks with edges into the reference {len(w)} | of which none in graph {fmt(len(z), len(w))} | edges {sum(x[1] for v in w.values() for x in v)}/{sum(len(v) for v in w.values())}")
        if d_ == "rt_out_gold": GOLD_IN = (w, set(z))
        else: BASE_IN = (w, set(z))
    # (c)
    q = [i for i in ids if sym[i]]
    allz = [i for i in q if all(tuple(r["nb"]) == ("ok", 0) for r in sym[i])]
    sfx = [r for i in q for r in sym[i] if r["kind"] == "suffix"]
    print(f"  (c) tasks with extracted symbols {len(q)} | all symbols ok/0 {fmt(len(allz), len(q))} | short names (suffix match) ok/0 {fmt(sum(1 for r in sfx if tuple(r['nb'])==('ok',0)), len(sfx))}")
    # R7 composite: (a) reference function absent (b) all incoming edges into the reference absent (when observed in either base or gold traces) (c) all issue symbols ok/0
    a = set(none); b = BASE_IN[1] | GOLD_IN[1]
    b_def = set(BASE_IN[0]) | set(GOLD_IN[0])
    # (b) is cleared if either trace saw an edge that is in the graph
    b = {i for i in b if not any(x[1] for x in (BASE_IN[0].get(i, []) + GOLD_IN[0].get(i, [])))}
    c = set(allz)
    anyx = a | b | c
    print(f"  R7 composite (denominator {len(ids)} tasks):")
    print(f"     (a) reference function node absent {fmt(len(a & set(ids)), len(ids))}")
    print(f"     (b) runtime edges into the reference: 0 in graph {fmt(len(b), len(ids))}  ({len(b)} of {len(b_def)} tasks where defined)")
    print(f"     (c) all issue symbols ok/0 {fmt(len(c), len(ids))}")
    print(f"     any {fmt(len(anyx), len(ids))} | all three {len(a & b & c)}")
    # b_def: tasks where at least one incoming edge into the reference was observed in a trace. Part 2 strata separate
    # "not exposed (incoming edge in graph)" from "incoming edge not observed" (exposure = a OR b, fixed 2026-10-05)
    return {"ids": ids, "a": sorted(a), "b": sorted(b), "c": sorted(c), "b_def": sorted(b_def)}

out = {"strict": report("strict (reference run passes all)", STRICT), "relaxed": report("relaxed (0 tests newly broken by the reference)", RELAX),
       "all": report("all 129 (reference only)", set(tasks))}
json.dump(out, open(S + "/part1_stats.json", "w"), ensure_ascii=False, indent=0)
