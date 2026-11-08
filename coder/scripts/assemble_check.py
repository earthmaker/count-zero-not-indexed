"""81 tasks x 4 conditions: assemble from per-run results.jsonl, count tasks/dups/missing, check vs permutation."""
import json, sys, csv, collections, os
R = os.environ.get("G4P_WORK", ".")
RUNS = ["v6_confirm1", "v8_confirm2", "v9_confirm3", "v10_confirm4", "v11_confirm5"]
CONDS = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
order = list(csv.DictReader(open(f"{R}/derived/part2_order.tsv"), delimiter="\t"))
pos = {r["instance_id"]: int(r["order"]) for r in order}
strat = {r["instance_id"]: (r["repo"], r["stratum"]) for r in order}
rows = []
for run in RUNS:
    for c in CONDS:
        p = f"{R}/runs/{run}/out/{c}/results.jsonl"
        traces = set(os.listdir(f"{R}/runs/{run}/out/{c}/traces"))
        for line in open(p):
            if not line.strip(): continue
            d = json.loads(line)
            assert d["bundle"] == c, (run, c, d["bundle"])
            d["run"] = run
            d["has_trace"] = f"trace_{d['id']}.json" in traces
            rows.append(d)
key = collections.Counter((d["id"], d["bundle"]) for d in rows)
dups = {k: v for k, v in key.items() if v > 1}
ids = {d["id"] for d in rows}
print("rows", len(rows), "distinct tasks", len(ids), "dup (task,cond)", len(dups), dups)
print("not in permutation:", sorted(ids - set(pos)))
print("permutation tasks missing:", sorted(set(pos) - ids, key=pos.get))
for c in CONDS:
    s = {d["id"] for d in rows if d["bundle"] == c}
    print(c, "n", len(s), "missing", sorted(set(pos) - s), "no-trace", sum(not d["has_trace"] for d in rows if d["bundle"] == c))
# run -> positions contiguous?
for run in RUNS:
    ps = sorted({pos[d["id"]] for d in rows if d["run"] == run})
    print(run, "positions", ps[0], "-", ps[-1], "n", len(ps), "contiguous", ps == list(range(ps[0], ps[-1] + 1)))
    per = collections.Counter(d["bundle"] for d in rows if d["run"] == run)
    print("   per-cond", dict(per))
# task appears in >1 run?
tr = collections.defaultdict(set)
for d in rows: tr[d["id"]].add(d["run"])
print("tasks in >1 run:", {k: v for k, v in tr.items() if len(v) > 1})
# descriptive table
print("\nstrata of 81:", collections.Counter(s for _, s in strat.values()), collections.Counter(strat.values()))
print("\nresolved / error rows per condition")
for c in CONDS:
    rs = [d for d in rows if d["bundle"] == c]
    print(c, "resolved", sum(d["resolved"] for d in rs), "/", len(rs),
          "exit-1", sum(d["exit"] == -1 for d in rs), "error", sum(bool(d.get("error")) for d in rs))
# per-run resolved
print("\nresolved by run x cond")
for run in RUNS:
    print(run, [sum(d["resolved"] for d in rows if d["run"] == run and d["bundle"] == c) for c in CONDS])
with open(f"{R}/table_81x4.tsv", "w") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["order", "instance_id", "repo", "stratum", "run"] + [f"{c}_resolved" for c in CONDS] + [f"{c}_exit" for c in CONDS])
    by = {(d["id"], d["bundle"]): d for d in rows}
    for r in order:
        i = r["instance_id"]
        w.writerow([r["order"], i, r["repo"], r["stratum"], by[(i, CONDS[0])]["run"]] +
                   [int(by[(i, c)]["resolved"]) for c in CONDS] + [by[(i, c)]["exit"] for c in CONDS])
print("wrote table_81x4.tsv")
