"""End of Part 1, three outputs: (1) name alignment rate (manuscript section 4.2) (2) R7 as defined in the manuscript (any reference function with a, b or c) (3) two human audit queues.
The audit queues contain competition data (source lines), so they are written only outside this release (G4P_AUDIT).
  align_queue.tsv  : aligner check N_align, stratified sample of machine labels (mapped / unmapped:<reason>)
  edge_queue.tsv   : edge classifier check N_audit, sample stratified by category x in-graph, with call-site source line attached
Human columns: human_label (right/wrong/unsure), human_note. Seed SEED fixed.
"""
import collections, csv, glob, json, os, random, re, tarfile
S = os.environ["G4"]; SEED = 20261005   # S = work folder
OUT = os.environ.get("G4P_AUDIT", "audit")
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(S + "/part/tasks.jsonl")}
gc = {r["id"]: r for r in json.load(open(S + "/gold_check.json"))}
RELAX = sorted(i for i, r in gc.items() if r["verdict"] == "judgeable" or r.get("relaxed"))
STRICT = sorted(i for i, r in gc.items() if r["verdict"] == "judgeable")
def modname(p):
    p = p[:-3]; p = p[4:] if p.startswith("src/") else p; p = p[:-9] if p.endswith("/__init__") else p
    return p.replace("/", ".")
def is_lib(p):
    return p.endswith(".py") and not re.search(r"(^|/)(tests?|testing|docs_src|docs|scripts)/|(^|/)(test_[^/]*|conftest|_swegemma_stubs)\.py$", p)
def wilson(k, n, z=1.96):
    import math
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return (c-h)/d, (c+h)/d
def graph(t):
    g = json.load(open(glob.glob(f"{S}/full/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json")[0]))
    return {n["name"] for n in g["nodes"]}, {(e["source"], e["target"]) for e in g["edges"]}

# (1) alignment rate: share of traced library functions (excluding module bodies) mapped to a graph node name
fn_rows, edge_rows = [], []
A = collections.Counter()
for i in RELAX:
    f = f"{S}/rt_out/{i}.json"
    if not os.path.exists(f): continue
    d = json.load(open(f)); gn, ge = graph(tasks[i])
    for n in d["nodes"]:
        if not is_lib(n["path"]) or n["qualname"] == "<module>": continue
        name = modname(n["path"]) + "." + n["qualname"]
        if name in gn: lab = "mapped"
        elif n.get("is_lambda_or_comp") or re.search(r"<(lambda|genexpr|listcomp|dictcomp|setcomp)>", n["qualname"]): lab = "unmapped:lambda_comp"
        elif "<locals>" in n["qualname"]: lab = "unmapped:nested"
        elif n.get("is_async"): lab = "unmapped:async"
        else: lab = "unmapped:other"
        A[lab] += 1; fn_rows.append({"id": i, "path": n["path"], "qualname": n["qualname"], "lineno": n["lineno"], "graph_name": name, "machine": lab})
    meta = {(n["path"], n["qualname"], n["lineno"]): n for n in d["nodes"]}
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
        edge_rows.append({"id": i, "caller": cn, "callee": dn, "caller_path": cp, "call_line": e["line"], "callee_path": dp,
                          "callee_def_line": dl, "in_graph": (cn, dn) in ge, "machine": k,
                          "ends_in_graph": cn in gn and dn in gn})
tot = sum(A.values()); m = A["mapped"]; lo, hi = wilson(m, tot)
print(f"(1) alignment rate (relaxed {len(RELAX)} tasks, base traces) traced library functions {tot} | mapped {m} ({m/tot:.1%}, {lo:.1%}-{hi:.1%})")
for k, v in A.most_common(): print(f"     {k:22s} {v}")
# excluding lambda/comprehension (units the graph does not hold by design)
core = tot - A["unmapped:lambda_comp"]; print(f"     excluding lambdas/comprehensions {m}/{core} ({m/core:.1%}) | remaining unmapped (other) {A['unmapped:other']}")

# (2) R7 as in the manuscript: any reference function (sync, class, async, nested) with (a) no node (b) a node but neighbors ok/0 (c) at least one missed traced adjacent edge
r7b = json.load(open(S + "/r7b.json")); ok0 = {(x["id"], x["node"]) for x in r7b["gold"] if tuple(x["nb"]) == ("ok", 0)}
gold = collections.defaultdict(list)
for r in json.load(open(S + "/gold_vs_graph.json")):
    if r["cat"] in ("function", "async", "nested", "class"): gold[r["id"]].append(r)
def r7(ids, tag):
    a = b = c = anyx = n = 0; per = {}
    for i in ids:
        if not gold[i]: continue
        n += 1
        A_ = any(not r["hit"] for r in gold[i])
        B_ = any(r["hit"] and (i, modname(r["path"]) + "." + r["q"]) in ok0 for r in gold[i])
        gnames = {modname(r["path"]) + "." + r["q"] for r in gold[i] if r["hit"]}
        C_ = False
        for dd in ("rt_out", "rt_out_gold"):
            f = f"{S}/{dd}/{i}.json"
            if not os.path.exists(f): continue
            for e in [x for x in edge_rows if x["id"] == i] if dd == "rt_out" else []:
                if (e["caller"] in gnames or e["callee"] in gnames) and not e["in_graph"]: C_ = True
        a += A_; b += B_; c += C_; anyx += (A_ or B_ or C_); per[i] = (A_, B_, C_)
    f = lambda k: f"{k}/{n} ({k/n:.1%}, {wilson(k,n)[0]:.1%}–{wilson(k,n)[1]:.1%})"
    print(f"(2) R7 manuscript definition [{tag}] tasks with a reference function {n}: (a) {f(a)} | (b) {f(b)} | (c) {f(c)} | any {f(anyx)}")
    return per
r7(STRICT, "strict"); r7(RELAX, "relaxed")

# (3) audit queues
rnd = random.Random(SEED)
def srcline(iid, path, ln, cache={}):
    k = iid
    if k not in cache:
        cache.clear(); cache[k] = tarfile.open(f"{S}/full/snapshots/{iid}.tgz")
    tf = cache[k]
    for cand in (path, "./" + path):
        try:
            txt = tf.extractfile(cand).read().decode("utf-8", "replace").splitlines()
            return txt[ln - 1].strip()[:200] if 0 < ln <= len(txt) else ""
        except (KeyError, AttributeError):
            continue
    return "(source not found)"
def strat(rows, key, per):
    by = collections.defaultdict(list)
    for r in rows: by[key(r)].append(r)
    out = []
    for k in sorted(by): out += rnd.sample(by[k], min(per, len(by[k])))
    return out
al = strat(fn_rows, lambda r: r["machine"], 20)
ed = strat(edge_rows, lambda r: (r["machine"], r["in_graph"]), 12)
for r in sorted(al, key=lambda r: r["id"]): r["def_src"] = srcline(r["id"], r["path"], r["lineno"])
for r in sorted(ed, key=lambda r: r["id"]): r["call_src"] = srcline(r["id"], r["caller_path"], r["call_line"]); r["callee_def_src"] = srcline(r["id"], r["callee_path"], r["callee_def_line"])
def dump(name, rows, cols, ask):
    with open(f"{OUT}/{name}", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["n"] + cols + ["human_label", "human_note"])
        for j, r in enumerate(rows, 1): w.writerow([j] + [r.get(c, "") for c in cols] + ["", ""])
    print(f"(3) {OUT}/{name} - {len(rows)} rows | question: {ask}")
rnd.shuffle(al); rnd.shuffle(ed)    # shuffled so the human does not read in machine-label order
dump("align_queue.tsv", al, ["id", "path", "lineno", "qualname", "def_src", "graph_name", "machine"],
     "is the machine label (mapped = that function is the graph_name node / unmapped:reason) correct?")
dump("edge_queue.tsv", ed, ["id", "caller", "call_line", "call_src", "callee", "callee_def_src", "machine", "in_graph", "ends_in_graph"],
     "is the machine category (plain, decorated, name_not_on_line, async, nested) correct given the call-site source?")
print("strata (alignment):", dict(collections.Counter(r["machine"] for r in al)))
print("strata (edges):", dict(collections.Counter((r["machine"], r["in_graph"]) for r in ed)))
