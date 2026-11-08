"""Gemma4Paper Part 2 -- descriptive (preregistered-as-descriptive) and exploratory measures for the 81 tasks.
Not part of the frozen confirmatory analysis. Reuses the frozen script's functions read-only (no redefinition of events).
Labels: [REG-DESC] = the preregistration asks for this as a descriptive report (no test);
        [REG-EXPL] = registered as exploratory (10-11 log); [EXPL] = not in the preregistration at all.
Usage: python3 -I descriptive_exploratory.py <frozen confirm_p1p5.py> <coder dir> <derived dir> <rows.jsonl> <out.json> <run>/out ..."""
import sys, json, re, importlib.util, collections, math
from pathlib import Path
frozen, coder, derived, rowsf, outf, *runs = sys.argv[1:]
spec = importlib.util.spec_from_file_location("cp", frozen); cp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp)
te = cp.load_te(coder)
CONDS = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
GRAPH = {"search_similar_code", "get_code_neighbors", "get_code_subgraph"}
order, goldq = cp.read_sample(derived)
samp = {r["instance_id"]: r for r in order}
rows = [json.loads(l) for l in open(rowsf)]
W = lambda x, n: [round(v, 3) for v in cp.wilson(x, n)] if n else None
out = {}

# [REG-DESC] graph-call task rate per condition (10-06 log: "A's graph call rate = new descriptive result, rate + interval")
trajs = {}
for run in runs:
    run = Path(run)
    for c in CONDS:
        for l in open(run / c / "results.jsonl"):
            t = json.loads(l)["id"]
            trajs[(t, c)] = te.load_steps(json.load(open(run / c / "traces" / f"trace_{t}.json")))
assert len(trajs) == 324, len(trajs)
g = {}
for c in CONDS:
    n_task = sum(any(s["k"] == "call" and s["name"] in GRAPH for s in trajs[(t, c)]) for t in samp)
    n_calls = sum(sum(s["k"] == "call" and s["name"] in GRAPH for s in trajs[(t, c)]) for t in samp)
    n_tool = sum(sum(s["k"] == "call" for s in trajs[(t, c)]) for t in samp)
    g[c] = {"tasks_with_graph_call": n_task, "n": 81, "wilson95": W(n_task, 81), "graph_calls": n_calls, "tool_calls": n_tool}
out["REG-DESC graph_call_rate"] = g

# [REG-DESC] A_beh curve over k in {1,2,3,5,8} (section 2) -- E_empty events and gold-function events; C and D (+A,B counts)
curve = {}
for c in CONDS:
    curve[c] = {}
    for k in (1, 2, 3, 5, 8):
        ne = nb = ng = ngb = 0
        task_any_gold_beh = collections.Counter(); task_n = collections.Counter()
        for t in samp:
            seq = trajs[(t, c)]
            gold = cp.gold_names(goldq.get(t, []))
            anyg = False
            for e in te.code_events(seq, None, k):
                if e["event"] == "E_empty":
                    ne += 1; nb += e["A_beh"]
                names = set()
                for q in e["query"]:
                    names |= cp.event_names(te, q)
                if names & gold:
                    ng += 1; ngb += e["A_beh"]; anyg |= e["A_beh"]
            st = samp[t]["stratum"]; task_n[st] += 1; task_any_gold_beh[st] += anyg
        curve[c][k] = {"E_empty": ne, "E_empty_A_beh": nb, "gold_events": ng, "gold_events_A_beh": ngb,
                       "tasks_any_gold_A_beh": dict(task_any_gold_beh), "tasks": dict(task_n)}
out["REG-DESC A_beh_k_curve"] = curve

# [REG-EXPL] extended-vocabulary A_lang (10-11 log; coder/a_lang_sensitivity.py pattern verbatim)
ALT = re.compile(te.ABSENCE.pattern + r"|(did ?n[o']t|did not) (return|find|yield|show) (anything|any|results?)|still nothing|returned (an )?empty|(came|comes) back empty", re.I)
def count_alang(pattern):
    old = te.ABSENCE; te.ABSENCE = pattern
    try:
        res = {}
        for c in CONDS:
            ne = nl = ng = ngl = 0; tasks_gold = collections.Counter()
            for t in samp:
                seq = trajs[(t, c)]; calls = [i for i, x in enumerate(seq) if x["k"] == "call"]
                gold = cp.gold_names(goldq.get(t, [])); hit = False
                for e in te.code_events(seq, None, 3):
                    if e["event"] == "E_empty":
                        ne += 1; nl += e["A_lang"]
                    names = set()
                    for q in e["query"]:
                        names |= cp.event_names(te, q)
                    if names & gold:
                        texts = cp.window_texts(seq, calls, e["call_idx"], calls[e["call_idx"]], 3)
                        h = bool(cp.a_lang_hits(te, texts, names)); ng += 1; ngl += h; hit |= h
                tasks_gold[samp[t]["stratum"]] += hit
            res[c] = {"E_empty": ne, "E_empty_A_lang": nl, "gold_events": ng, "gold_events_A_lang": ngl,
                      "tasks_gold_A_lang": dict(tasks_gold)}
        return res
    finally:
        te.ABSENCE = old
out["REG-EXPL A_lang_vocab_0.2"] = count_alang(te.ABSENCE)
out["REG-EXPL A_lang_vocab_extended"] = count_alang(ALT)

# [EXPL] event-level X after E_empty (P3 at event level)
ev = {}
for c in CONDS:
    ne = nx = 0
    for t in samp:
        for e in te.code_events(trajs[(t, c)], None, 3):
            if e["event"] == "E_empty":
                ne += 1; nx += e["X"]
    ev[c] = {"E_empty": ne, "followed_by_X": nx, "rate": round(nx / ne, 3) if ne else None, "wilson95_naive": W(nx, ne)}
out["EXPL P3_event_level"] = ev

# [EXPL] P3 tasks with E_empty in only one condition (eligibility asymmetry)
R = {(r["task"], r["cond"]): r for r in rows}
only_c = [t for t in samp if R[(t, "C_graphfirst")]["n_empty"] > 0 and R[(t, "D_guard_graphfirst")]["n_empty"] == 0]
only_d = [t for t in samp if R[(t, "D_guard_graphfirst")]["n_empty"] > 0 and R[(t, "C_graphfirst")]["n_empty"] == 0]
out["EXPL P3_eligibility"] = {"E_empty_in_C_only": len(only_c), "z_C_among_them": sum(R[(t, "C_graphfirst")]["empty_then_X"] for t in only_c),
                              "E_empty_in_D_only": len(only_d), "z_D_among_them": sum(R[(t, "D_guard_graphfirst")]["empty_then_X"] for t in only_d),
                              "neither": sum(R[(t, "C_graphfirst")]["n_empty"] == 0 and R[(t, "D_guard_graphfirst")]["n_empty"] == 0 for t in samp)}

# [EXPL] resolution by repo x condition, by run x condition, error kinds
rep = collections.defaultdict(dict)
for repo in ("fastapi", "rich", "requests"):
    ts = [t for t in samp if samp[t]["repo"] == repo]
    for c in CONDS:
        rep[repo][c] = f"{sum(R[(t, c)]['resolved'] for t in ts)}/{len(ts)}"
out["EXPL resolved_by_repo"] = rep
byrun = collections.defaultdict(dict)
for r in rows:
    byrun[r["run"]].setdefault(r["cond"], [0, 0]); byrun[r["run"]][r["cond"]][0] += r["resolved"]; byrun[r["run"]][r["cond"]][1] += 1
out["EXPL resolved_by_run"] = {k: {c: f"{v[0]}/{v[1]}" for c, v in d.items()} for k, d in byrun.items()}
out["EXPL error_kinds"] = {c: dict(collections.Counter(r["error_kind"] or ("exit-1" if r["exit"] == -1 else "none")
                                                      for r in rows if r["cond"] == c)) for c in CONDS}
out["EXPL resolved_any_condition"] = sum(any(R[(t, c)]["resolved"] for c in CONDS) for t in samp)
out["EXPL resolved_all_conditions"] = sum(all(R[(t, c)]["resolved"] for c in CONDS) for t in samp)
out["EXPL resolved_by_stratum"] = {c: {s: f"{sum(R[(t, c)]['resolved'] for t in samp if samp[t]['stratum']==s)}/{sum(samp[t]['stratum']==s for t in samp)}"
                                       for s in ("exposed", "covered")} for c in CONDS}
Path(outf).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False))
