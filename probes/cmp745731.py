"""Our Part 1 (b) runtime-edge recall vs. the call traces of forum post 745731 (Akhil Chinta), side by side with the same scoring rule. Runs locally.
A: their traces (1 commit per repository, full suite, unique pairs) | B: our rt_out (per-task test_patch, multi-count, unique pairs per repository) | C: overlapping pairs."""
import json, glob, os, re, collections
H = os.environ.get("G4P_WORK", ".")
TR = os.path.join(H, "cmp745731")   # put trace_*.json of akhilchinta1505/code-graph-call-traces here (kaggle CLI 2.x datasets download)
tasks = {json.loads(l)["instance_id"]: json.loads(l) for l in open(H + "/data/tasks.jsonl")}

def modname(path):
    p = path[:-3]
    if p.startswith("src/"): p = p[4:]
    if p.endswith("/__init__"): p = p[:-9]
    return p.replace("/", ".")

def is_lib(path):
    return path.endswith(".py") and not re.search(r"(^|/)(tests?|testing|docs_src|docs|scripts)/|(^|/)(test_[^/]*|conftest|_swegemma_stubs)\.py$", path)

GC = {}
def graph(repo, sha):
    k = f"{repo}_{sha}"
    if k not in GC:
        g = json.load(open(f"{H}/data/graphs/{k}.json"))
        GC[k] = ({n["name"] for n in g["nodes"]}, {(e["source"], e["target"]) for e in g["edges"]})
    return GC[k]

def rec(pairs, gn, ge):
    pairs = list(pairs)
    n = len(pairs); h = sum((a, b) in ge or (b, a) in ge for a, b in pairs)
    both = [(a, b) for a, b in pairs if a in gn and b in gn]
    hb = sum((a, b) in ge or (b, a) in ge for a, b in both)
    return n, h, (h / n if n else 0), len(both), (hb / len(both) if both else 0)

out = {}
# A: their traces
A = {}
for f in sorted(glob.glob(TR + "/trace_*.json")):
    repo, sha = re.match(r".*/trace_(\w+?)_([0-9a-f]{40})\.json$", f).groups()
    if not os.path.exists(f"{H}/data/graphs/{repo}_{sha}.json"): continue
    gn, ge = graph(repo, sha)
    raw = {tuple(e) for e in json.load(open(f))}
    lib = lambda x: x.startswith(repo + ".")
    pairs = {(a, b) for a, b in raw if lib(a) and lib(b)}          # library<->library (dispatch, docs_src, tests excluded)
    A[repo] = (sha, pairs)
    out[f"A {repo} lib-lib unique pairs"] = rec(pairs, gn, ge)
    out[f"A {repo} all raw traces (incl. dispatch)"] = rec(raw, gn, ge)

# B: our traces
Bm = collections.defaultdict(list); Bu = collections.defaultdict(set); Bsame = collections.defaultdict(set)
for iid, t in tasks.items():
    f = f"{H}/rt_out/{iid}.json"
    if not os.path.exists(f): continue
    repo = t["repo"].split("/")[1]
    gn, ge = graph(repo, t["base_commit"])
    d = json.load(open(f))
    nm = {(n["path"], n["qualname"], n["lineno"]): n for n in d["nodes"]}
    for e in d["edges"]:
        (cp, cq, cl), (dp, dq, dl) = e["caller"], e["callee"]
        if not (is_lib(cp) and is_lib(dp)) or "<module>" in (cq, dq): continue
        m = nm.get((dp, dq, dl), {})
        if m.get("is_lambda_or_comp") or "<lambda>" in dq or "<genexpr>" in dq or "comp>" in dq: continue
        p = (modname(cp) + "." + cq, modname(dp) + "." + dq)
        hit = p in ge
        Bm[repo].append(hit)
        Bu[(repo, t["base_commit"])].add(p)
        if repo in A and t["base_commit"] == A[repo][0]: Bsame[repo].add(p)
for repo in sorted({r for r, _ in Bu}):
    hits = Bm[repo]
    out[f"B {repo} multi-count (our manuscript method)"] = (len(hits), sum(hits), sum(hits) / len(hits), None, None)
    # unique pairs: judged against each commit's graph and summed
    n = h = 0
    for (r, sha), ps in Bu.items():
        if r != repo: continue
        gn, ge = graph(r, sha); n += len(ps); h += sum(p in ge or p[::-1] in ge for p in ps)
    out[f"B {repo} per-commit unique pairs, summed"] = (n, h, h / n if n else 0, None, None)
    if Bsame[repo]:
        gn, ge = graph(repo, A[repo][0])
        out[f"B {repo} unique pairs, tasks at their commit only"] = rec(Bsame[repo], gn, ge)
    # C: overlap = all our unique pairs (by name) intersected with their pairs, on their commit's graph
    if repo in A:
        sha, ap = A[repo]; gn, ge = graph(repo, sha)
        ours = set().union(*[ps for (r, _), ps in Bu.items() if r == repo])
        inter = ours & ap
        out[f"C {repo} overlap (ours & theirs) on their graph"] = rec(inter, gn, ge)
        out[f"C {repo} theirs only"] = rec(ap - ours, gn, ge)
        out[f"C {repo} ours only (on their commit graph)"] = rec(ours - ap, gn, ge)
print(f"{'item':44s} {'n':>7s} {'hit':>6s} {'recall':>7s} {'n_both_nodes':>10s} {'recall_within':>9s}")
for k, (n, h, r, nb, rb) in out.items():
    print(f"{k:44s} {n:7d} {h:6d} {r:7.1%} " + (f"{nb:10d} {rb:9.1%}" if nb is not None else ""))
json.dump({k: list(v) for k, v in out.items()}, open(TR + "/cmp_result.json", "w"), ensure_ascii=False, indent=1)
