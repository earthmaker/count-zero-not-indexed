"""Part 2 confirmatory run readout (descriptive): counts resolution, graph calls and judge events per condition from result jsonl and traces.
Args: <run>/out folder [--rt <rt_out directory>]. With --rt, get_code_neighbors results are matched against runtime trace edges
and split into E_full / E_incomplete / E_full_untraced (traced in trace_events.code_events). Without it, all are E_full_untraced.
P1-P4 tests are produced only after all tasks finish, as pre-registered; this table is for progress checks only."""
import json, sys, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace_events as te
A = [a for a in sys.argv[1:]]
RT = os.path.expanduser(A.pop(A.index("--rt") + 1)) if "--rt" in A else None
A = [a for a in A if a != "--rt"]
R = os.path.expanduser(A[0] if A else "runs/v6_confirm1/out")
GRAPH = {"search_similar_code", "get_code_neighbors", "get_code_subgraph"}
B = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
rows = {}
for b in B:
    for l in open(f"{R}/{b}/results.jsonl"):
        r = json.loads(l); rows[(b, r["id"])] = r
tasks = list(dict.fromkeys(r["id"] for (b, _), r in rows.items() if b == "A_baseline"))
print("rules", te.RULES_VERSION, "k", te.K_DEFAULT, "rt", RT or "none")
_rt = {}
def traced_for(t):
    if RT is None:
        return None
    if t not in _rt:
        f = os.path.join(RT, f"{t}.json")
        _rt[t] = te.traced_neighbors(te.Path(f)) if os.path.exists(f) else {}
        summ_rt["rt_files"] += os.path.exists(f)
    return _rt[t]
summ_rt = collections.Counter()
summ = {b: collections.Counter() for b in B}
per = []
for t in tasks:
    line = [t]
    for b in B:
        r = rows[(b, t)]
        traj = json.load(open(f"{R}/{b}/traces/trace_{t}.json"))
        seq = te.load_steps(traj)
        g = sum(1 for s in seq if s["k"] == "call" and s["name"] in GRAPH)
        ev = te.code_events(seq, traced_for(t), te.K_DEFAULT)
        sr = te.self_report(seq)
        c = summ[b]
        c["n"] += 1; c["resolved"] += r["resolved"]; c["exit_m1"] += r["exit"] == -1
        c["ctx_overflow"] += bool(r.get("error") and "ContextWindowExceeded" in r["error"])
        c["other_error"] += bool(r.get("error") and "ContextWindowExceeded" not in r["error"])
        c["graph_calls"] += g; c["tasks_with_graph"] += g > 0
        for e in ev:
            c["ev_" + e["event"]] += 1
            if e["event"] == "E_empty":
                c["empty_A_lang"] += bool(e["A_lang"]); c["empty_A_beh"] += bool(e["A_beh"]); c["empty_X"] += bool(e["X"])
        c["task_has_empty"] += any(e["event"] == "E_empty" for e in ev)
        c["task_empty_then_X"] += any(e["event"] == "E_empty" and e["X"] for e in ev)
        c["S_claim"] += bool(sr["S_claim"]); c["S_claim_unresolved"] += bool(sr["S_claim"]) and not r["resolved"]
        c["tool_calls"] += r["tool_calls"]; c["sec"] += r["sec"]
        line.append(f"{'R' if r['resolved'] else ('x' if r['exit']==-1 else '.')}{g:>2}")
    per.append(line)
print("task".ljust(16), "  ".join(b[:1] for b in B), "   (R resolved, . unresolved, x exit-1, digit = graph calls)")
for l in per:
    print(l[0].ljust(16), " ".join(l[1:]))
keys = sorted({k for c in summ.values() for k in c})
print()
print("metric".ljust(20), "".join(b[:12].rjust(14) for b in B))
for k in keys:
    print(k.ljust(20), "".join(f"{summ[b][k]:>14.1f}" if isinstance(summ[b][k], float) else f"{summ[b][k]:>14}" for b in B))
if RT is not None:
    print("runtime trace files", summ_rt["rt_files"], "/", len(tasks))
# Pairs: resolution discordance
for x, y in [("A_baseline", "B_guard"), ("C_graphfirst", "D_guard_graphfirst"), ("A_baseline", "C_graphfirst")]:
    b_ = sum(rows[(x, t)]["resolved"] and not rows[(y, t)]["resolved"] for t in tasks)
    c_ = sum(rows[(y, t)]["resolved"] and not rows[(x, t)]["resolved"] for t in tasks)
    print(f"resolution discordance only {x[:1]} {b_} | only {y[:1]} {c_}")
