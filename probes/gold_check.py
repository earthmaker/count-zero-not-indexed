"""End of Part 1: compares reference-patch runs (rt_out_gold) with base runs (rt_out) via junit and counts judgeable tasks.
Judgeable = reference patch applies, all test_patch tests pass on the reference run (0 failures/errors, collection ok), and at least one test failing on base (F2P >= 1).
"""
import json, os, collections, xml.etree.ElementTree as ET
S = os.environ["G4"]   # work folder (part/, full/, rt_out/, rt_out_gold/)
tasks = [json.loads(l) for l in open(S + "/part/tasks.jsonl")]
def junit(p):
    if not os.path.exists(p): return None
    try: r = ET.parse(p).getroot()
    except ET.ParseError: return None
    out = {}
    for tc in r.iter("testcase"):
        k = tc.get("classname", "") + "::" + tc.get("name", "")
        st = "pass"
        for ch in tc:
            if ch.tag in ("failure", "error"): st = "fail"
            elif ch.tag == "skipped" and st == "pass": st = "skip"
        out[k] = st
    errs = sum(int(s.get("errors", 0)) for s in r.iter("testsuite"))
    return out, errs
rows = []; C = collections.Counter()
for t in tasks:
    i = t["instance_id"]
    mb = json.load(open(f"{S}/rt_out/{i}.meta.json")); mg = json.load(open(f"{S}/rt_out_gold/{i}.meta.json"))
    jb = junit(f"{S}/rt_out/{i}.junit.xml"); jg = junit(f"{S}/rt_out_gold/{i}.junit.xml")
    r = {"id": i, "repo": t["repo"], "commit": t["base_commit"], "gold_apply": mg.get("gold_apply_rc"), "tp_apply": mg.get("apply_rc"),
         "rc_base": mb.get("rc"), "rc_gold": mg.get("rc")}
    if jg:
        g, ge = jg; r["gold_n"] = len(g); r["gold_fail"] = sum(v == "fail" for v in g.values()); r["gold_pass"] = sum(v == "pass" for v in g.values())
    if jb and jg:
        b, _ = jb; g, _ = jg
        r["f2p"] = sum(1 for k, v in g.items() if v == "pass" and b.get(k, "fail") == "fail")
        r["p2p"] = sum(1 for k, v in g.items() if v == "pass" and b.get(k) == "pass")
    elif jg and not jb:
        r["f2p"] = r.get("gold_pass", 0); r["base_collect_fail"] = True
    if r["gold_apply"] != 0: v = "reference patch failed to apply"
    elif r["rc_gold"] == "timeout": v = "reference run timeout"
    elif not jg or r.get("gold_n", 0) == 0: v = "reference run collection failed"
    elif r["gold_fail"]: v = "failing tests after reference patch"
    elif not r.get("f2p"): v = "F2P 0 (also passes on base)"
    else: v = "judgeable"
    r["verdict"] = v; C[v] += 1; rows.append(r)
json.dump(rows, open(S + "/gold_check.json", "w"), ensure_ascii=False, indent=0)
for k, n in C.most_common(): print(f"{n:4d}  {k}")
print("judgeable by repository:", dict(collections.Counter(r["repo"] for r in rows if r["verdict"] == "judgeable")), "/ all", dict(collections.Counter(r["repo"] for r in rows)))
for r in rows:
    if r["verdict"] != "judgeable": print(" ", r["id"], r["verdict"], "rc_base", r["rc_base"], "rc_gold", r["rc_gold"], "gold_n", r.get("gold_n"), "fail", r.get("gold_fail"))

# Relaxed rule: every failing test on the reference run also failed on base (dead for environment reasons) and F2P >= 1
print("\nrelaxed rule (0 tests newly broken by the reference, F2P >= 1):")
relax = 0
for r in rows:
    if r["verdict"] != "failing tests after reference patch": continue
    b = junit(f"{S}/rt_out/{r['id']}.junit.xml"); g, _ = junit(f"{S}/rt_out_gold/{r['id']}.junit.xml")
    bb = b[0] if b else {}
    broke = [k for k, v in g.items() if v == "fail" and bb.get(k) == "pass"]
    newfail = [k for k, v in g.items() if v == "fail" and k not in bb]
    r["relaxed"] = bool(b) and not broke and not newfail and r.get("f2p", 0) > 0
    relax += r["relaxed"]
    print(f"  {r['id']:15s} f2p {r.get('f2p')} broken_by_reference {len(broke)} new_fail_not_in_base {len(newfail)} base_collect {'ok' if b else 'failed'} -> {'included' if r['relaxed'] else 'excluded'}")
print("strict", C["judgeable"], "| relaxed", C["judgeable"] + relax)
json.dump(rows, open(S + "/gold_check.json", "w"), ensure_ascii=False, indent=0)
