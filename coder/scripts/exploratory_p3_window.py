"""[EXPL] Not in the preregistration. P3 manipulation check under other windows (k in 1,2,3,5,8 and to end of
trajectory), same eligible-pair rule as the frozen script; E_empty events with any utterance in the k=3 window;
condition-C bridge counts (gold-function events that were empty). Events come from the frozen judge 0.2 unchanged.
Usage: python3 -I exploratory_p3_window.py <frozen confirm_p1p5.py> <coder dir> <derived dir> <out.json> <run>/out ..."""
import sys, json, importlib.util
from pathlib import Path
frozen, coder, derived, outf, *runs = sys.argv[1:]
spec = importlib.util.spec_from_file_location("cp", frozen); cp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp)
te = cp.load_te(coder)
order, goldq = cp.read_sample(derived)
samp = {r["instance_id"]: r for r in order}
traj = {}
for run in runs:
    for c in ("C_graphfirst", "D_guard_graphfirst", "A_baseline", "B_guard"):
        for l in open(Path(run) / c / "results.jsonl"):
            t = json.loads(l)["id"]
            traj[(t, c)] = te.load_steps(json.load(open(Path(run) / c / "traces" / f"trace_{t}.json")))
assert len(traj) == 324
out = {}
def z_of(seq, k):
    ev = [e for e in te.code_events(seq, None, k) if e["event"] == "E_empty"]
    return (any(e["X"] for e in ev) if ev else None)
for k in (1, 2, 3, 5, 8, 10**6):
    a = b = c = d = 0
    for t in samp:
        zc, zd = z_of(traj[(t, "C_graphfirst")], k), z_of(traj[(t, "D_guard_graphfirst")], k)
        if zc is None or zd is None: continue
        if zc and zd: a += 1
        elif zd and not zc: b += 1
        elif zc and not zd: c += 1
        else: d += 1
    n = a + b + c + d
    out[f"P3_DvC_k{'_to_end' if k == 10**6 else k}"] = {"pairs": n, "a_both": a, "b_D_only": b, "c_C_only": c, "d_neither": d,
        "z_C": round((a + c) / n, 3), "z_D": round((a + b) / n, 3), "mcnemar_p": cp.exact_mcnemar(b, c)}
# utterance in k=3 window after E_empty (all conditions)
tot = lang = 0
for (t, c), seq in traj.items():
    calls = [i for i, x in enumerate(seq) if x["k"] == "call"]
    for e in te.code_events(seq, None, 3):
        if e["event"] != "E_empty": continue
        tot += 1
        texts = cp.window_texts(seq, calls, e["call_idx"], calls[e["call_idx"]], 3)
        lang += any(x.strip() for x in texts)
out["E_empty_with_utterance_in_k3_window_all_conditions"] = f"{lang}/{tot}"
# bridge: gold-function events in C and D, task level
for c in ("C_graphfirst", "D_guard_graphfirst"):
    tasks_gold = tasks_all_empty = tasks_nonempty = 0; per_stratum = {"exposed": [0, 0], "covered": [0, 0]}
    for t in samp:
        gold = cp.gold_names(goldq.get(t, []))
        evs = []
        for e in te.code_events(traj[(t, c)], None, 3):
            names = set()
            for q in e["query"]: names |= cp.event_names(te, q)
            if names & gold: evs.append(e)
        if not evs: continue
        tasks_gold += 1; s = samp[t]["stratum"]; per_stratum[s][0] += 1
        if all(e["event"] == "E_empty" for e in evs): tasks_all_empty += 1; per_stratum[s][1] += 1
        else: tasks_nonempty += 1
    out[f"bridge_{c}"] = {"tasks_with_gold_event": tasks_gold, "tasks_all_gold_events_empty": tasks_all_empty,
                          "tasks_some_gold_event_nonempty": tasks_nonempty,
                          "by_stratum_[with_gold, all_empty]": per_stratum}
Path(outf).write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
