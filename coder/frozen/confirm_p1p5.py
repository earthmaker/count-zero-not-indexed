"""Gemma4Paper Part 2 -- confirmatory analysis of preregistered hypotheses P1-P5 (frozen version).
Frozen before all 81 confirmatory tasks were run (39/81 done; permutation positions 40+ not yet run).

Preregistration: Contest_Gemma4Paper_설계_2부사전등록.md (section 1 table, 2, 3, 4, 4-1, 6 and the change log:
10-06 conditions C/D added, P1 measured in C, P3/P4 measured as D vs C; 10-10 harness pinned, P2 undecidable when
A_lang is absent; 10-11 extended A_lang vocabulary is exploratory only; 10-12 this script).
Event definitions come unchanged from the frozen judge trace_events.py (RULES_VERSION 0.2, k = 3). This file does
not redefine events; it only fixes how events are aggregated per task and which tests decide each hypothesis.

Usage (paths are arguments; nothing machine-specific is hard-coded)
  python3 confirm_p1p5.py build   --coder <dir with trace_events.py> --derived <dir> --out rows.jsonl <run>/out ...
  python3 confirm_p1p5.py analyze --derived <dir> --out <dir> rows.jsonl      # -> results.json, results.md, p1_hits.jsonl
  python3 confirm_p1p5.py selftest --coder <dir> [<run>/out ...]               # synthetic controls + numeric checks
  --coder defaults to the directory of this file; --derived defaults to ./derived (relative to the working directory).
  <derived> must contain part2_order.tsv and gold_vs_graph.json.

Verdict labels: support / oppose / inconclusive / not decidable.
All intervals are 95% (alpha = .05 two-sided). No randomness: the same input gives the same output.

---------------------------------------------------------------------------------------------------------------
Hypothesis -> condition -> test
  P1  Exposed tasks reach absence conclusions (A_lang) about the gold function more often. Condition C (10-06).
      Task-level y = 1 if ANY graph event whose query names a gold-function symbol has A_lang true (same "any"
      rule as P3). Group 1 = exposed, group 0 = covered. Denominator = all decidable tasks of the stratum
      (section 3 power table "47 vs 34"); a task without a gold event has y = 0.
      Test: repository-stratified exact conditional test of a common odds ratio of 1 (= exact Mantel-Haenszel,
      convolution of per-stratum hypergeometrics; as R mantelhaen.test(exact = TRUE)). Chosen over "Fisher
      combination by repository" because the decision rule needs "the 95% interval of the difference" and a
      combination of Fisher p-values yields no interval; the exact conditional test inverts to an exact interval.
      Two-sided p = 2 x min(one-sided p) (NOT the R "minimum likelihood" two-sided p; values can differ).
      Decision interval: exact conditional 95% CI of the common odds ratio, read on the log scale
      (above 0 -> support, below 0 -> oppose, contains 0 -> inconclusive). Equivalent to two-sided p < .05.
      Also reported (no decision): MH risk difference with Sato (1989) variance, its rule-based verdict
      `rd_verdict`, and `scale_agree`; if the two scales disagree the table says so (decision stays on OR).
      Note: section 3 power was computed one-sided at .05; the decision here is two-sided 95%, so the minimum
      detectable difference is larger than the section 3 table.
      Also reported per stratum: tasks with a gold event, tasks with a gold event followed by an utterance.
      Reference rows (no decision): (a) conditional on opportunity (denominator = tasks with gold event +
      utterance), (b) E_empty events only, (c) strict symbol rule (no owner/outer expansion; tasks whose gold
      names are all dunders excluded).
  P2  Tasks with an absence conclusion fail verification more often: P(V|A) - P(V|not A). Condition C.
      A = A_lang true on any graph event (any symbol; the preregistered wording has no gold restriction).
      V = not resolved. Same stratified exact test (group 1 = A tasks). First reported number = MH risk
      difference (the registered metric); decision on the OR interval as P1. Error rows per group reported.
      Reference row: error rows (exit -1 or error) excluded.
  P3  The guard increases grep cross-checks after empty results (manipulation check). Primary D vs C (10-06);
      auxiliary B vs A. Task-level z = "any X within k = 3 after an E_empty". z is defined only for tasks with
      >= 1 E_empty in that condition (10-06 log: "P3 undefined when E_empty is rare"); pairs = tasks with E_empty
      in both conditions. Exact McNemar on discordant pairs (b = guard only, c = control only), two-sided
      p = 2 x binomial tail (capped at 1). Decision (mapping not in the plan's text; stated in the 10-12 log):
      p < .05 and b > c -> support; c > b -> oppose; else inconclusive. Paired difference with Newcombe (1998)
      method 10 interval reported. Reference row: literal version with z = 0 for tasks without E_empty.
  P4  The guard does not reduce resolution. Primary D - C paired; auxiliary B - A. No non-inferiority margin is
      registered, so only an interval: Newcombe (1998) paired method 10. Lower > 0 -> support (improvement, the
      only case the plan allows "improved"); upper < 0 -> oppose; else inconclusive (no margin, so "does not
      reduce" cannot be established; the word "non-inferior" is not used). b, c and exact McNemar p reported.
      Reference row: pairs with an error row on either side excluded.
  P5  Self-report mismatch (S_claim and not resolved) concentrates in exposed tasks. Condition A. "Interval only."
      Task-level indicator = S_claim and not resolved, denominator = all decidable tasks of the stratum.
      Interval: unstratified difference of proportions (exposed - covered), Newcombe (1998) method 10.
      Lower > 0 -> support, upper < 0 -> oppose, else inconclusive. Per stratum: claim rate and unresolved rate.
      Reference rows: conditional on S_claim; repository-stratified MH risk difference (rich is 23 vs 5).

"Not decidable" -- only when an estimator has no denominator, or the change log names an absence of opportunity
  no decidable task; one group empty; P2: no task with A_lang (10-11 log); P3: no eligible pair (10-06 log);
  P4: no pair; P1: no task has a gold-function graph event, or no gold event is followed by any utterance in its
  window (10-10 log, "not decidable for lack of opportunity").
  Zero outcome events with opportunity present is NOT "not decidable": the interval rule applies (inconclusive),
  and per-stratum opportunity counts and Wilson upper bounds are reported (section 1 promise to report nulls).

Sample, missing data, exclusions
  1. Only the registered 81 tasks (part2_order.tsv: exposed 47 + covered 34). Any other task (unobserved 28,
     pilot v4, smoke tests v3/v5, auxiliary arms) stops `build`: pass confirmatory run folders only.
  2. A duplicated (task, condition, replicate) stops `build`. Replicates r >= 2 are excluded from the primary
     analysis and only counted -- even if r = 2 is completed for all 81 tasks, it stays auxiliary.
  3. Error rows (exit -1, ContextWindowExceeded, ...) are kept with the harness `resolved` (intention to treat);
     events are counted if a trajectory exists. Error rows = exit == -1 or a non-empty error. P2/P4 are also
     reported without error rows (reference).
  4. Missing or unreadable trajectory: the row leaves event-based measures (P1, P2, P3, P5) and stays in P4.
  5. P3/P4 pairs need both condition rows; unpaired tasks are counted.
  6. If the task set is not a prefix of the permutation (section 4), a warning is written to the results.
  7. Gold-function symbols (P1), from gold_vs_graph.json rows with cat in {function, class, async, nested}:
     for each qualname, its last identifier; if that is a dunder, the owning class instead; if the qualname
     contains <locals>, also the function right before the first <locals>.
     Event side, the same mapping: the judge's short name of the query, plus -- when the query is a dotted path
     whose last component is a dunder -- the component before it (code-snippet queries keep the short name only).
     A gold event = an event with a name in the gold set. Its A_lang is re-measured with the 0.2 window,
     sentence split and ABSENCE vocabulary, restricted to the names of the matching queries. Tasks without gold
     symbols are excluded from P1 and counted. The re-implemented window is checked against 0.2's A_lang on every
     event (build and selftest stop on any mismatch).
  8. A_lang uses the frozen 0.2 vocabulary only. The extended vocabulary (10-11) is exploratory and not used.
  9. Auxiliary arms (proxy model, 0.2.11 with thinking) never enter P1-P5 decisions.

Interpretation points fixed here (recorded in the 10-12 change log)
  - P2 in C (it uses P1's outcome as its explanatory variable); P5 in A (it uses no graph event and was not moved
    on 10-06). Other conditions are reported in an auxiliary table without decisions. Auxiliary P2 in B/D: the guard
    prompt itself says an empty result "means UNCONFIRMED, not 'does not exist'"; an agent echoing it can trigger
    A_lang, so B/D P2 values are not interpretable as absence conclusions.
  - P1 decision scale = common odds ratio; risk difference shown alongside.
  - Task-level outcome = "any event" (P1, P2, P3 alike), not "first event".
"""
import csv
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ANALYSIS_VERSION = "1.1"
ALPHA = 0.05
Z = 1.959963984540054        # standard normal 0.975 quantile
CONDS = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
PRIMARY = {"P1": "C_graphfirst", "P2": "C_graphfirst", "P3": ("C_graphfirst", "D_guard_graphfirst"),
           "P4": ("C_graphfirst", "D_guard_graphfirst"), "P5": "A_baseline"}
AUX_PAIR = ("A_baseline", "B_guard")
GOLD_CATS = {"function", "class", "async", "nested"}
HERE = Path(__file__).resolve().parent
SUPPORT, OPPOSE, HOLD, UNDET = "support", "oppose", "inconclusive", "not decidable"
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def load_te(coder=None):
    d = Path(coder) if coder else HERE
    if not (d / "trace_events.py").exists():
        raise SystemExit(f"trace_events.py not found in {d} (use --coder)")
    sys.path.insert(0, str(d.resolve()))
    import trace_events as te
    if not str(te.RULES_VERSION).startswith("0.2"):
        raise SystemExit(f"judge version is not 0.2.x: {te.RULES_VERSION}")
    return te


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def is_error_row(r):
    return r.get("exit") == -1 or bool(r.get("error_kind"))


# ----------------------------------------------------------------- statistics (no dependencies)
def _lcomb(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _lse(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def _stratum_logpmf(n1, n0, m, lpsi):
    """Noncentral hypergeometric: group sizes n1, n0, outcome total m, log odds ratio lpsi -> {x: log P(x)}."""
    lo, hi = max(0, m - n0), min(n1, m)
    lw = {x: _lcomb(n1, x) + _lcomb(n0, m - x) + x * lpsi for x in range(lo, hi + 1)}
    z = _lse(list(lw.values()))
    return {x: v - z for x, v in lw.items()}


def _conv_logpmf(strata, lpsi):
    dist = {0: 0.0}
    for (n1, n0, m) in strata:
        p = _stratum_logpmf(n1, n0, m, lpsi)
        new = {}
        for a, la in dist.items():
            for b, lb in p.items():
                new.setdefault(a + b, []).append(la + lb)
        dist = {k: _lse(v) for k, v in new.items()}
    return dist


def _tail(dist, t, upper):
    xs = [v for k, v in dist.items() if (k >= t if upper else k <= t)]
    return math.exp(_lse(xs)) if xs else 0.0


def exact_stratified(tables):
    """tables: [(x1, n1, x0, n0)] per stratum. Exact conditional test of common OR = 1 and exact conditional
    95% CI. Uninformative strata (one group empty, or all/no outcomes) are dropped.
    Two-sided p = min(1, 2 * min(p_upper, p_lower))."""
    info = [(x1, n1, x0, n0) for (x1, n1, x0, n0) in tables if n1 > 0 and n0 > 0 and 0 < x1 + x0 < n1 + n0]
    if not info:
        return {"informative_strata": 0, "or_ci95": [0.0, math.inf], "log_or_ci95": [-math.inf, math.inf],
                "p_two_sided": 1.0, "p_method": "2 x min(one-sided), conditional"}
    strata = [(n1, n0, x1 + x0) for (x1, n1, x0, n0) in info]
    t = sum(x1 for (x1, _, _, _) in info)
    tmin = sum(max(0, m - n0) for (n1, n0, m) in strata)
    tmax = sum(min(n1, m) for (n1, n0, m) in strata)
    d0 = _conv_logpmf(strata, 0.0)
    p_up, p_lo = _tail(d0, t, True), _tail(d0, t, False)
    p2 = min(1.0, 2 * min(p_up, p_lo))

    def solve(f, target):           # f increasing in lpsi
        a, b = -60.0, 60.0
        for _ in range(200):
            c = (a + b) / 2
            if f(c) < target:
                a = c
            else:
                b = c
        return (a + b) / 2
    a2 = ALPHA / 2
    lo = -math.inf if t == tmin else solve(lambda l: _tail(_conv_logpmf(strata, l), t, True), a2)
    hi = math.inf if t == tmax else solve(lambda l: -_tail(_conv_logpmf(strata, l), t, False), -a2)
    if t == tmin:
        lmle = -math.inf
    elif t == tmax:
        lmle = math.inf
    else:                           # conditional MLE: conditional expectation = t
        lmle = solve(lambda l: sum(math.exp(v) * k for k, v in _conv_logpmf(strata, l).items()), t)

    def ex(v):
        return 0.0 if v == -math.inf else (math.inf if v == math.inf else math.exp(v))
    return {"informative_strata": len(info), "T": t, "T_range": [tmin, tmax], "p_upper": p_up, "p_lower": p_lo,
            "p_two_sided": p2, "p_method": "2 x min(one-sided), conditional", "or_cmle": ex(lmle),
            "or_ci95": [ex(lo), ex(hi)], "log_or_ci95": [lo, hi]}


def mh_risk_difference(tables):
    """MH risk difference (group 1 - group 0) with Sato (1989) variance, 95% CI. Descriptive.
    Degenerate (zero-width) when every stratum has zero events."""
    num = den = sp = sq = 0.0
    for (x1, n1, x0, n0) in tables:
        N = n1 + n0
        if n1 == 0 or n0 == 0:
            continue
        num += (x1 * n0 - x0 * n1) / N
        den += n1 * n0 / N
        sp += (n1 * n1 * x0 - n0 * n0 * x1 + n1 * n0 * (n0 - n1) / 2) / (N * N)
        sq += (x1 * (n0 - x0) + x0 * (n1 - x1)) / (2 * N)
    if den == 0:
        return None
    rd = num / den
    var = (rd * sp + sq) / (den * den)
    se = math.sqrt(max(var, 0.0))
    return {"rd": rd, "ci95": [rd - Z * se, rd + Z * se], "method": "MH risk difference, Sato (1989) variance"}


def wilson(x, n):
    if n == 0:
        return (math.nan, math.nan)
    p = x / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def newcombe_unpaired(x1, n1, x0, n0):
    """Newcombe (1998) method 10 -- difference of independent proportions p1 - p0."""
    p1, p0 = x1 / n1, x0 / n0
    l1, u1 = wilson(x1, n1)
    l0, u0 = wilson(x0, n0)
    d = p1 - p0
    return d, [d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)]


def newcombe_paired(a, b, c, d):
    """Newcombe (1998) paired method 10. a = both 1, b = treatment only, c = control only, d = both 0.
    Difference = p_treatment - p_control."""
    n = a + b + c + d
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = wilson(a + b, n)
    l2, u2 = wilson(a + c, n)
    den = (a + b) * (c + d) * (a + c) * (b + d)
    phi = (a * d - b * c) / math.sqrt(den) if den > 0 else 0.0
    th = p1 - p2
    dl = math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    du = math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return th, [th - dl, th + du]


def exact_mcnemar(b, c):
    """Exact McNemar: two-sided p = min(1, 2 * binomial(b + c, 1/2) lower tail at min(b, c))."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)


def ci_verdict(lo, hi, zero=0.0):
    if lo > zero:
        return SUPPORT
    if hi < zero:
        return OPPOSE
    return HOLD


# ----------------------------------------------------------------- readout (trajectory -> task x condition row)
def _dunder(s):
    return s.startswith("__") and s.endswith("__")


def gold_names(qualnames, strict=False):
    """Gold-function names. Expanded: last identifier (dunder -> owning class) + the function right before the
    first <locals>. Strict: last identifier only, dunders dropped, no expansion."""
    out = set()
    for q in qualnames:
        parts = q.split(".")
        last = parts[-1]
        if strict:
            if not _dunder(last) and IDENT.fullmatch(last):
                out.add(last)
            continue
        if _dunder(last):
            if len(parts) >= 2 and IDENT.fullmatch(parts[-2]):
                out.add(parts[-2])
        elif IDENT.fullmatch(last):
            out.add(last)
        if "<locals>" in q:
            outer = q.split(".<locals>")[0].split(".")[-1]
            if IDENT.fullmatch(outer):
                out.add(outer)
    return out


def event_names(te, q, strict=False):
    """Names an event query refers to: the judge's short name; plus, for a dotted-path query ending in a dunder,
    the component before it (the owner). Code-snippet queries keep the short name only."""
    s = te.short(q)
    names = {s} if s else set()
    if strict:
        return names
    raw = re.sub(r"\(.*$", "", str(q), flags=re.S).strip().strip("`'\"")
    if not re.search(r"\s", raw):
        parts = raw.split(".")
        if len(parts) >= 2 and _dunder(parts[-1]) and IDENT.fullmatch(parts[-2]):
            names.add(parts[-2])
    return names


def window_texts(seq, calls, ci, i, k):
    """Same window as trace_events.code_events: next k calls, utterances up to the call after them (or the end)."""
    end = calls[ci + 1 + k] if ci + 1 + k < len(calls) else len(seq)
    return [x["text"] for x in seq[i + 1:end] if x["k"] == "msg"]


def a_lang_hits(te, texts, syms):
    """0.2 A_lang expression with a chosen symbol set: sentences holding a symbol and an ABSENCE phrase."""
    out = []
    for t in texts:
        for sent in re.split(r"(?<=[.!?\n])\s+", t):
            if te.ABSENCE.search(sent) and any(re.search(r"\b" + re.escape(s) + r"\b", sent) for s in syms):
                out.append(sent)
    return out


def task_measures(te, traj, gold, gold_strict=frozenset(), k=None):
    """One trajectory -> task-level measures. gold / gold_strict: gold-function name sets."""
    k = te.K_DEFAULT if k is None else k
    seq = te.load_steps(traj)
    ev = te.code_events(seq, None, k)
    calls = [i for i, x in enumerate(seq) if x["k"] == "call"]
    m = {"gold_events": 0, "gold_lang_opportunity": 0, "gold_alang_events": 0,
         "gold_empty_events": 0, "gold_empty_alang_events": 0,
         "gold_events_strict": 0, "gold_lang_opportunity_strict": 0, "gold_alang_events_strict": 0}
    hits, mismatch = [], 0
    for e in ev:
        ci = e["call_idx"]
        texts = window_texts(seq, calls, ci, calls[ci], k)
        if bool(a_lang_hits(te, texts, e["short"])) != e["A_lang"]:
            mismatch += 1                       # window re-implementation must equal 0.2
        has_lang = any(t.strip() for t in texts)
        for sfx, strict, gset in [("", False, gold), ("_strict", True, gold_strict)]:
            syms = set()
            for q in e["query"]:
                qn = event_names(te, q, strict)
                if qn & gset:
                    syms |= qn
            if not syms:
                continue
            h = a_lang_hits(te, texts, syms)
            m["gold_events" + sfx] += 1
            m["gold_lang_opportunity" + sfx] += has_lang
            m["gold_alang_events" + sfx] += bool(h)
            if not strict:
                if e["event"] == "E_empty":
                    m["gold_empty_events"] += 1
                    m["gold_empty_alang_events"] += bool(h)
                if h:
                    hits.append({"call_idx": ci, "event": e["event"], "query": e["query"], "names": sorted(syms),
                                 "sentences": [s[:300] for s in h]})
    sr = te.self_report(seq)
    empties = [e for e in ev if e["event"] == "E_empty"]
    return dict(m, n_graph_events=len(ev), n_empty=len(empties), any_A_lang=any(e["A_lang"] for e in ev),
                empty_then_X=any(e["X"] for e in empties), gold_A_lang=m["gold_alang_events"] > 0,
                gold_A_lang_empty=m["gold_empty_alang_events"] > 0,
                gold_A_lang_strict=m["gold_alang_events_strict"] > 0,
                S_claim=bool(sr["S_claim"]), recheck_mismatch=mismatch, gold_hits=hits)


def read_sample(derived):
    order = list(csv.DictReader(open(Path(derived) / "part2_order.tsv"), delimiter="\t"))
    gold = {}
    for x in json.load(open(Path(derived) / "gold_vs_graph.json")):
        if x["cat"] in GOLD_CATS:
            gold.setdefault(x["id"], []).append(x["q"])
    return order, gold


def build(argv):
    out = Path(_opt(argv, "--out", "rows.jsonl"))
    derived = Path(_opt(argv, "--derived", "derived"))
    te = load_te(_opt(argv, "--coder"))
    order, goldq = read_sample(derived)
    samp = {r["instance_id"]: r for r in order}
    seen, rows = set(), []
    for run in argv:
        run = Path(os.path.expanduser(run))
        for cond in CONDS:
            f = run / cond / "results.jsonl"
            if not f.exists():
                continue
            for line in open(f):
                r = json.loads(line)
                t, rep = r["id"], int(r.get("rep", 1))
                if t not in samp:
                    raise SystemExit(f"task {t} ({run}) is outside the registered 81 -- pass confirmatory runs only (rule 1)")
                key = (t, cond, rep)
                if key in seen:
                    raise SystemExit(f"duplicate row {key} -- refusing to pick one silently (rule 2)")
                seen.add(key)
                err = r.get("error") or ""
                row = {"task": t, "repo": samp[t]["repo"], "stratum": samp[t]["stratum"], "order": int(samp[t]["order"]),
                       "cond": cond, "rep": rep, "run": run.parent.name if run.name == "out" else run.name,
                       "resolved": bool(r["resolved"]), "exit": r.get("exit"),
                       "error_kind": ("" if not err else ("ContextWindowExceeded" if "ContextWindowExceeded" in err else "other")),
                       "gold_names": sorted(gold_names(goldq.get(t, []))),
                       "gold_names_strict": sorted(gold_names(goldq.get(t, []), strict=True))}
                tf = run / cond / "traces" / f"trace_{t}.json"
                try:
                    m = task_measures(te, json.load(open(tf)), set(row["gold_names"]), set(row["gold_names_strict"]))
                    row.update(trace_ok=True, **m)
                except (OSError, json.JSONDecodeError, KeyError, TypeError) as ex:
                    row.update(trace_ok=False, trace_error=type(ex).__name__)
                rows.append(row)
    bad = sum(r.get("recheck_mismatch", 0) for r in rows)
    if bad:
        raise SystemExit(f"A_lang window re-implementation disagrees with 0.2 on {bad} events -- stop")
    with open(out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta = {"analysis_version": ANALYSIS_VERSION, "rules_version": te.RULES_VERSION, "k": te.K_DEFAULT,
            "trace_events_sha256": sha256(te.__file__), "part2_order_sha256": sha256(derived / "part2_order.tsv"),
            "gold_vs_graph_sha256": sha256(derived / "gold_vs_graph.json"),
            "runs": [Path(a).parent.name if Path(a).name == "out" else Path(a).name for a in argv], "n_rows": len(rows)}
    Path(str(out) + ".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"build: {len(rows)} rows -> {out}")
    return rows


# ----------------------------------------------------------------- analysis
def _strat_tables(rows, group, outcome):
    """rows -> per-repository (x1, n1, x0, n0)."""
    by = {}
    for r in rows:
        t = by.setdefault(r["repo"], [0, 0, 0, 0])
        if group(r):
            t[0] += bool(outcome(r)); t[1] += 1
        else:
            t[2] += bool(outcome(r)); t[3] += 1
    return {k: tuple(v) for k, v in sorted(by.items())}


def _strat_result(tables, base):
    """Stratified exact test + OR-interval verdict. Not decidable only without a denominator."""
    tl = list(tables.values())
    n1 = sum(t[1] for t in tl); n0 = sum(t[3] for t in tl)
    x1 = sum(t[0] for t in tl); x0 = sum(t[2] for t in tl)
    res = dict(base, strata={k: {"x1": v[0], "n1": v[1], "x0": v[2], "n0": v[3]} for k, v in tables.items()},
               x1=x1, n1=n1, x0=x0, n0=n0,
               wilson1=list(wilson(x1, n1)) if n1 else None, wilson0=list(wilson(x0, n0)) if n0 else None)
    ex = exact_stratified(tl)
    res["exact"] = ex
    rd = mh_risk_difference(tl)
    res["mh_rd"] = rd
    if n1 + n0 == 0:
        res.update(verdict=UNDET, reason="no decidable task")
        return res
    if n1 == 0 or n0 == 0:
        res.update(verdict=UNDET, reason=f"one group empty (group1 {n1}, group0 {n0})")
        return res
    lo, hi = ex["log_or_ci95"]
    res["verdict"] = ci_verdict(lo, hi)
    if ex["informative_strata"] == 0:
        res["reason"] = (f"no informative stratum (outcome events {x1 + x0}/{n1 + n0}: all strata degenerate) -- "
                         "exact OR CI [0, inf], inconclusive by the interval rule; see Wilson upper bounds")
    else:
        res["reason"] = "exact conditional 95% CI of the common OR (log scale vs 0)"
    res["rd_verdict"] = ci_verdict(*rd["ci95"]) if rd else None
    res["scale_agree"] = (res["rd_verdict"] == res["verdict"]) if rd else None
    if rd and not res["scale_agree"]:
        res["reason"] += f"; SCALE DISAGREEMENT -- risk difference rule gives '{res['rd_verdict']}' (decision stays on OR)"
    return res


def _by_stratum(rows, key):
    return {s: sum(bool(r[key]) for r in rows if r["stratum"] == s) for s in ("exposed", "covered")}


def _p1_core(rr, outcome, base):
    tables = _strat_tables(rr, lambda r: r["stratum"] == "exposed", outcome)
    return _strat_result(tables, base)


def analyze_p1(rows, cond):
    base = {"P": "P1", "cond": cond,
            "test": "repo-stratified exact conditional test (exact MH); group1 exposed / group0 covered; outcome gold-function A_lang"}
    rr = [r for r in rows if r["cond"] == cond and r.get("trace_ok")]
    no_gold = [r["task"] for r in rr if not r["gold_names"]]
    rr = [r for r in rr if r["gold_names"]]
    opp = {"tasks": {s: sum(r["stratum"] == s for r in rr) for s in ("exposed", "covered")},
           "gold_event": {s: sum(r["stratum"] == s and r["gold_events"] > 0 for r in rr) for s in ("exposed", "covered")},
           "gold_event_and_utterance": {s: sum(r["stratum"] == s and r["gold_lang_opportunity"] > 0 for r in rr)
                                        for s in ("exposed", "covered")}}
    base.update(excluded_no_gold=len(no_gold), opportunity_by_stratum=opp)
    res = _p1_core(rr, lambda r: r["gold_A_lang"], base)
    n_ev = sum(opp["gold_event"].values())
    n_lang = sum(opp["gold_event_and_utterance"].values())
    if res["verdict"] != UNDET:
        if n_ev == 0:
            res.update(verdict=UNDET, reason="lack of opportunity (10-10 log): no task has a gold-function graph event")
        elif n_lang == 0:
            res.update(verdict=UNDET, reason="lack of opportunity (10-10 log): no gold-function event is followed by an utterance")
    # reference rows (no decision)
    ref = {}
    ro = [r for r in rr if r["gold_lang_opportunity"] > 0]
    ref["conditional_on_opportunity"] = _p1_core(ro, lambda r: r["gold_A_lang"], {"note": "reference; denominator = tasks with gold event + utterance"})
    ref["E_empty_only"] = _p1_core(rr, lambda r: r["gold_A_lang_empty"], {"note": "reference; gold events that are E_empty only"})
    rs = [r for r in rows if r["cond"] == cond and r.get("trace_ok") and r["gold_names_strict"]]
    ref["strict_symbols"] = _p1_core(rs, lambda r: r["gold_A_lang_strict"],
                                     {"note": "reference; strict names (no owner/outer expansion, dunder-only tasks excluded)",
                                      "gold_event_strict": _by_stratum([dict(r, g=r["gold_events_strict"] > 0) for r in rs], "g")})
    res["reference"] = ref
    return res


def analyze_p2(rows, cond, with_reference=True):
    base = {"P": "P2", "cond": cond,
            "test": "repo-stratified exact conditional test (exact MH); group1 tasks with A_lang / group0 others; outcome not resolved (V)"}
    rr = [r for r in rows if r["cond"] == cond and r.get("trace_ok")]
    tables = _strat_tables(rr, lambda r: r["any_A_lang"], lambda r: not r["resolved"])
    res = _strat_result(tables, base)
    res["error_rows"] = {"A": sum(is_error_row(r) for r in rr if r["any_A_lang"]),
                         "notA": sum(is_error_row(r) for r in rr if not r["any_A_lang"])}
    if rr and res["n1"] == 0:
        res.update(verdict=UNDET, reason=f"no task with A_lang (0/{len(rr)}) -- P(V|A) has no denominator (10-11 log)")
    if with_reference:
        res["reference"] = {"error_rows_excluded": analyze_p2([r for r in rows if not is_error_row(r)], cond, False)}
    return res


def _pairs(rows, ctrl, trt):
    by = {}
    for r in rows:
        by.setdefault(r["task"], {})[r["cond"]] = r
    both = {t: v for t, v in by.items() if ctrl in v and trt in v}
    return both, sum(1 for v in by.values() if (ctrl in v) != (trt in v))


def analyze_p3(rows, ctrl, trt, primary=True):
    both, unpaired = _pairs(rows, ctrl, trt)
    ok = {t: v for t, v in both.items() if v[ctrl].get("trace_ok") and v[trt].get("trace_ok")}
    elig = {t: v for t, v in ok.items() if v[ctrl]["n_empty"] > 0 and v[trt]["n_empty"] > 0}
    res = {"P": "P3", "cond": f"{trt} vs {ctrl}", "role": "primary" if primary else "auxiliary (no decision)",
           "test": "exact McNemar (two-sided); z = any X within k=3 after E_empty; pairs with E_empty in both conditions",
           "pairs_total": len(both), "pairs_trace_ok": len(ok), "unpaired_tasks": unpaired, "pairs_eligible": len(elig),
           "n_empty_ctrl": sum(v[ctrl]["n_empty"] for v in ok.values()),
           "n_empty_trt": sum(v[trt]["n_empty"] for v in ok.values()),
           "tasks_with_empty_ctrl": sum(v[ctrl]["n_empty"] > 0 for v in ok.values()),
           "tasks_with_empty_trt": sum(v[trt]["n_empty"] > 0 for v in ok.values())}
    lb = sum(v[trt]["empty_then_X"] and not v[ctrl]["empty_then_X"] for v in ok.values())
    lc = sum(v[ctrl]["empty_then_X"] and not v[trt]["empty_then_X"] for v in ok.values())
    res["reference"] = {"literal_all_pairs": {"n": len(ok), "b": lb, "c": lc, "p": exact_mcnemar(lb, lc),
                                              "note": "reference; z = 0 for tasks without E_empty"}}
    if not elig:
        res.update(verdict=UNDET, reason=f"no pair with E_empty in both conditions (E_empty events: control {res['n_empty_ctrl']}, guard {res['n_empty_trt']})")
        return res
    a = sum(v[trt]["empty_then_X"] and v[ctrl]["empty_then_X"] for v in elig.values())
    b = sum(v[trt]["empty_then_X"] and not v[ctrl]["empty_then_X"] for v in elig.values())
    c = sum(v[ctrl]["empty_then_X"] and not v[trt]["empty_then_X"] for v in elig.values())
    d = len(elig) - a - b - c
    p = exact_mcnemar(b, c)
    diff, ci = newcombe_paired(a, b, c, d)
    res.update(a=a, b=b, c=c, d=d, p_two_sided=p, p_method="exact binomial, 2 x min tail", paired_diff=diff,
               paired_diff_ci95=ci, ci_method="Newcombe (1998) paired method 10")
    if b + c == 0:
        res.update(verdict=HOLD, reason="no discordant pair")
    elif p < ALPHA:
        res.update(verdict=SUPPORT if b > c else OPPOSE, reason="exact McNemar two-sided p < .05")
    else:
        res.update(verdict=HOLD, reason="exact McNemar two-sided p >= .05")
    return res


def analyze_p4(rows, ctrl, trt, primary=True, with_reference=True):
    both, unpaired = _pairs(rows, ctrl, trt)
    res = {"P": "P4", "cond": f"{trt} - {ctrl}", "role": "primary" if primary else "auxiliary (no decision)",
           "test": "paired resolution difference; Newcombe (1998) paired method 10; no non-inferiority margin registered",
           "pairs": len(both), "unpaired_tasks": unpaired,
           "error_rows": {"trt": sum(is_error_row(v[trt]) for v in both.values()),
                          "ctrl": sum(is_error_row(v[ctrl]) for v in both.values())}}
    if with_reference:
        res["reference"] = {"error_rows_excluded": analyze_p4([r for r in rows if not is_error_row(r)], ctrl, trt, primary, False)}
    if not both:
        res.update(verdict=UNDET, reason="no pair")
        return res
    a = sum(v[trt]["resolved"] and v[ctrl]["resolved"] for v in both.values())
    b = sum(v[trt]["resolved"] and not v[ctrl]["resolved"] for v in both.values())
    c = sum(v[ctrl]["resolved"] and not v[trt]["resolved"] for v in both.values())
    d = len(both) - a - b - c
    diff, ci = newcombe_paired(a, b, c, d)
    res.update(a=a, b=b, c=c, d=d, resolved_trt=a + b, resolved_ctrl=a + c, diff=diff, ci95=ci,
               mcnemar_p=exact_mcnemar(b, c))
    v = ci_verdict(*ci)
    res.update(verdict=v, reason={SUPPORT: "interval lower bound > 0 -- improvement",
                                  OPPOSE: "interval upper bound < 0 -- resolution reduced",
                                  HOLD: "interval contains 0 -- no margin registered, 'does not reduce' cannot be established"}[v])
    return res


def analyze_p5(rows, cond):
    rr = [r for r in rows if r["cond"] == cond and r.get("trace_ok")]
    res = {"P": "P5", "cond": cond,
           "test": "unstratified difference of proportions (exposed - covered); Newcombe (1998) method 10; interval only"}
    g = {s: [r for r in rr if r["stratum"] == s] for s in ("exposed", "covered")}
    x = {s: sum(r["S_claim"] and not r["resolved"] for r in g[s]) for s in g}
    n = {s: len(g[s]) for s in g}
    cl = {s: sum(r["S_claim"] for r in g[s]) for s in g}
    un = {s: sum(not r["resolved"] for r in g[s]) for s in g}
    res.update(x_exposed=x["exposed"], n_exposed=n["exposed"], x_covered=x["covered"], n_covered=n["covered"],
               claim_exposed=cl["exposed"], claim_covered=cl["covered"],
               unresolved_exposed=un["exposed"], unresolved_covered=un["covered"],
               claim_rate={s: (cl[s] / n[s] if n[s] else None) for s in g},
               unresolved_rate={s: (un[s] / n[s] if n[s] else None) for s in g})
    if n["exposed"] == 0 or n["covered"] == 0:
        res.update(verdict=UNDET, reason=f"one stratum empty (exposed {n['exposed']}, covered {n['covered']})")
        return res
    diff, ci = newcombe_unpaired(x["exposed"], n["exposed"], x["covered"], n["covered"])
    res.update(diff=diff, ci95=ci, wilson_exposed=list(wilson(x["exposed"], n["exposed"])),
               wilson_covered=list(wilson(x["covered"], n["covered"])))
    ref = {"repo_stratified_mh_rd": dict(mh_risk_difference(list(_strat_tables(
        rr, lambda r: r["stratum"] == "exposed", lambda r: r["S_claim"] and not r["resolved"]).values())) or {},
        note="reference; MH risk difference by repository")}
    if cl["exposed"] and cl["covered"]:
        cd, cci = newcombe_unpaired(x["exposed"], cl["exposed"], x["covered"], cl["covered"])
        ref["conditional_on_claim"] = {"diff": cd, "ci95": cci, "note": "reference; denominator = S_claim tasks"}
    res["reference"] = ref
    res.update(verdict=ci_verdict(*ci), reason="95% interval of the difference (vs 0)"
               + ("; zero mismatch events -- see Wilson upper bounds" if x["exposed"] + x["covered"] == 0 else ""))
    return res


def analyze_rows(rows, order_ids=None):
    prim = [r for r in rows if r["rep"] == 1]
    tasks = sorted({r["task"] for r in prim})
    qa = {"n_rows": len(rows), "n_rows_rep_ge2_ignored": len(rows) - len(prim), "n_tasks": len(tasks),
          "rows_by_cond": {c: sum(r["cond"] == c for r in prim) for c in CONDS},
          "trace_missing_by_cond": {c: sum(r["cond"] == c and not r.get("trace_ok") for r in prim) for c in CONDS},
          "error_rows_by_cond": {c: sum(r["cond"] == c and is_error_row(r) for r in prim) for c in CONDS}}
    if order_ids is not None:
        qa["order_prefix_ok"] = set(tasks) == set(order_ids[:len(tasks)])
        if not qa["order_prefix_ok"]:
            qa["warning"] = "task set is not a prefix of the registered permutation (section 4)"
    res = {"P1": analyze_p1(prim, PRIMARY["P1"]), "P2": analyze_p2(prim, PRIMARY["P2"]),
           "P3": analyze_p3(prim, *PRIMARY["P3"]), "P4": analyze_p4(prim, *PRIMARY["P4"]),
           "P5": analyze_p5(prim, PRIMARY["P5"])}
    aux = {"P3_AB": analyze_p3(prim, *AUX_PAIR, primary=False), "P4_AB": analyze_p4(prim, *AUX_PAIR, primary=False)}
    for c in CONDS:
        if c != PRIMARY["P2"]:
            aux[f"P2_{c}"] = dict(analyze_p2(prim, c), role="auxiliary (no decision)")
        if c != PRIMARY["P5"]:
            aux[f"P5_{c}"] = dict(analyze_p5(prim, c), role="auxiliary (no decision)")
    return {"analysis_version": ANALYSIS_VERSION, "qa": qa, "primary": res, "auxiliary": aux}


def _f(v, nd=3):
    if v is None:
        return "-"
    if isinstance(v, float):
        if math.isinf(v):
            return "inf" if v > 0 else "-inf"
        return f"{v:.{nd}f}"
    return str(v)


def _ci(c):
    return f"[{_f(c[0])}, {_f(c[1])}]" if c else "-"


def summary_line(r):
    P = r["P"]
    if P in ("P1", "P2"):
        ex = r.get("exact", {})
        rd = r.get("mh_rd")
        s = (f"MH RD {_f(rd['rd'])} {_ci(rd['ci95'])}; " if (P == "P2" and rd) else "")
        s += f"group1 {r['x1']}/{r['n1']} (Wilson {_ci(r.get('wilson1'))}), group0 {r['x0']}/{r['n0']} (Wilson {_ci(r.get('wilson0'))})"
        s += f"; OR {_f(ex.get('or_cmle'))}, p {_f(ex.get('p_two_sided'))} (2 x min one-sided)"
        if P == "P1" and rd:
            s += f"; MH RD {_f(rd['rd'])} {_ci(rd['ci95'])}"
        if r.get("rd_verdict"):
            s += f"; RD rule: {r['rd_verdict']}"
        if P == "P1":
            o = r["opportunity_by_stratum"]
            s += (f"; opportunity exposed/covered: gold event {o['gold_event']['exposed']}/{o['gold_event']['covered']}, "
                  f"+utterance {o['gold_event_and_utterance']['exposed']}/{o['gold_event_and_utterance']['covered']}")
        if P == "P2":
            s += f"; error rows A {r['error_rows']['A']} / notA {r['error_rows']['notA']}"
        return s, "OR " + _ci(ex.get("or_ci95"))
    if P == "P3":
        if "b" not in r:
            return f"eligible pairs {r['pairs_eligible']}/{r['pairs_trace_ok']}; E_empty control {r['n_empty_ctrl']}, guard {r['n_empty_trt']}", "-"
        return (f"eligible pairs {r['pairs_eligible']}/{r['pairs_total']}; tasks with E_empty control {r['tasks_with_empty_ctrl']}, "
                f"guard {r['tasks_with_empty_trt']}; b {r['b']}, c {r['c']}, p {_f(r['p_two_sided'])}; diff {_f(r['paired_diff'])}",
                _ci(r["paired_diff_ci95"]))
    if P == "P4":
        if "b" not in r:
            return f"pairs {r['pairs']}", "-"
        return (f"pairs {r['pairs']}; resolved {r['resolved_trt']} vs {r['resolved_ctrl']}; b {r['b']}, c {r['c']}, "
                f"McNemar p {_f(r['mcnemar_p'])}; diff {_f(r['diff'])}", _ci(r["ci95"]))
    s = f"exposed {r['x_exposed']}/{r['n_exposed']}, covered {r['x_covered']}/{r['n_covered']}"
    if "diff" in r:
        s += (f"; diff {_f(r['diff'])}; claim rate {_f(r['claim_rate']['exposed'])}/{_f(r['claim_rate']['covered'])}, "
              f"unresolved rate {_f(r['unresolved_rate']['exposed'])}/{_f(r['unresolved_rate']['covered'])}")
    return s, _ci(r.get("ci95"))


def _ref_lines(name, r):
    out = []
    for k, v in (r.get("reference") or {}).items():
        if "P" in v:
            s, c = summary_line(v)
            out.append(f"| {name} {k} | {s} | {c} | {v.get('verdict')} |")
        elif "x1" in v:
            out.append(f"| {name} {k} | group1 {v['x1']}/{v['n1']}, group0 {v['x0']}/{v['n0']}; "
                       f"OR {_f(v['exact'].get('or_cmle'))} | OR {_ci(v['exact'].get('or_ci95'))} | {v.get('verdict')} |")
        else:
            out.append(f"| {name} {k} | {json.dumps({kk: vv for kk, vv in v.items() if kk not in ('ci95',)}, default=str)} | {_ci(v.get('ci95'))} | - |")
    return out


def to_md(out):
    m = out.get("meta", {})
    L = [f"# P1-P5 confirmatory analysis (analysis {out['analysis_version']}, judge {m.get('rules_version', '?')}, k {m.get('k', '?')})", "",
         "| P | condition | test | numbers | 95% interval | verdict | reason |", "|---|---|---|---|---|---|---|"]
    for k in ["P1", "P2", "P3", "P4", "P5"]:
        r = out["primary"][k]
        s, c = summary_line(r)
        L.append(f"| {k} | {r['cond']} | {r['test']} | {s} | {c} | **{r['verdict']}** | {r['reason']} |")
    L += ["", "## Reference rows (no decision)", "", "| row | numbers | interval | same rule would give |", "|---|---|---|---|"]
    for k in ["P1", "P2", "P3", "P4", "P5"]:
        L += _ref_lines(k, out["primary"][k])
    L += ["", "## Auxiliary conditions (no decision)", "", "| item | condition | numbers | 95% interval | same rule would give | reason |",
          "|---|---|---|---|---|---|"]
    for k, r in out["auxiliary"].items():
        s, c = summary_line(r)
        L.append(f"| {k} | {r['cond']} | {s} | {c} | {r['verdict']} | {r['reason']} |")
    L += ["", "Auxiliary P2 in B/D: the guard prompt says an empty result 'means UNCONFIRMED, not \"does not exist\"'; "
          "echoing it can trigger A_lang, so these values are not absence conclusions.", "",
          "## Sample checks", "", "```", json.dumps(out["qa"], ensure_ascii=False, indent=1), "```"]
    return "\n".join(L) + "\n"


def analyze(argv):
    outdir = Path(_opt(argv, "--out", "."))
    derived = Path(_opt(argv, "--derived", "derived"))
    rows = [json.loads(l) for l in open(argv[0])]
    op = derived / "part2_order.tsv"
    order_ids = [r["instance_id"] for r in csv.DictReader(open(op), delimiter="\t")] if op.exists() else None
    out = analyze_rows(rows, order_ids)
    mp = Path(str(argv[0]) + ".meta.json")
    out["meta"] = json.loads(mp.read_text()) if mp.exists() else {}
    out["meta"].update(rows_sha256=sha256(argv[0]), script_sha256=sha256(__file__), script_version=ANALYSIS_VERSION,
                       generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / "results.md").write_text(to_md(out))
    with open(outdir / "p1_hits.jsonl", "w") as fh:     # for hand labelling; decisions use the automatic counts
        for r in rows:
            if r["cond"] == PRIMARY["P1"] and r.get("gold_hits"):
                fh.write(json.dumps({"task": r["task"], "stratum": r["stratum"], "hits": r["gold_hits"]}, ensure_ascii=False) + "\n")
    print(f"analyze: -> {outdir}/results.json, results.md, p1_hits.jsonl")
    return out


# ----------------------------------------------------------------- selftest
def _row(task, repo, stratum, cond, resolved=False, gold_A=False, gold_ev=1, gold_lang=1, anyA=None, n_empty=0,
         eX=False, claim=False, order=1, rep=1, trace_ok=True, exit_=0, err=""):
    return {"task": task, "repo": repo, "stratum": stratum, "order": order, "cond": cond, "rep": rep, "run": "syn",
            "resolved": resolved, "exit": exit_, "error_kind": err, "gold_names": ["foo"], "gold_names_strict": ["foo"],
            "trace_ok": trace_ok, "n_graph_events": gold_ev, "n_empty": n_empty,
            "any_A_lang": gold_A if anyA is None else anyA, "empty_then_X": eX,
            "gold_events": gold_ev, "gold_lang_opportunity": gold_lang, "gold_alang_events": int(gold_A),
            "gold_empty_events": 0, "gold_empty_alang_events": 0, "gold_A_lang": gold_A, "gold_A_lang_empty": False,
            "gold_events_strict": gold_ev, "gold_lang_opportunity_strict": gold_lang, "gold_alang_events_strict": int(gold_A),
            "gold_A_lang_strict": gold_A, "S_claim": claim, "recheck_mismatch": 0, "gold_hits": []}


def _syn_p1(kind):
    """exposed 30 (fastapi 20, rich 10) / covered 30 (fastapi 20, rich 10), condition C."""
    rows, i = [], 0
    for repo, ne, nc in [("fastapi", 20, 20), ("rich", 10, 10)]:
        for s, n in [("exposed", ne), ("covered", nc)]:
            for j in range(n):
                i += 1
                if kind == "support":
                    a = j < (n * 8 // 10) if s == "exposed" else j < (n // 10)
                elif kind == "oppose":
                    a = j < (n // 10) if s == "exposed" else j < (n * 8 // 10)
                elif kind == "hold":
                    a = j < (n * 3 // 10)
                else:
                    a = False
                kw = {}
                if kind == "undet_noopp":
                    kw = {"gold_ev": 0, "gold_lang": 0}
                elif kind == "undet_nolang":
                    kw = {"gold_ev": 1, "gold_lang": 0}
                rows.append(_row(f"t{i}", repo, s, "C_graphfirst", resolved=not a and j % 3 == 0, gold_A=a, **kw))
    return rows


def _syn_pairs(kind, field):
    """60 tasks x (C, D). field = 'X' (P3) or 'R' (P4)."""
    rows = []
    for j in range(60):
        if kind == "support":
            ctrl, trt = j < 10, j < 40
        elif kind == "oppose":
            ctrl, trt = j < 40, j < 10
        elif kind == "hold":
            ctrl, trt = j < 20, (j < 18) or (40 <= j < 43)
        else:
            ctrl = trt = False
        ne = 0 if kind == "undet" else 2
        for c, v in [("C_graphfirst", ctrl), ("D_guard_graphfirst", trt)]:
            if field == "X":
                rows.append(_row(f"t{j}", "fastapi", "exposed", c, n_empty=ne, eX=v and ne > 0))
            else:
                rows.append(_row(f"t{j}", "fastapi", "exposed", c, resolved=v))
    if kind == "undet" and field == "R":
        rows = []
    return rows


def _syn_p5(kind):
    rows = []
    for j in range(40):
        s = "exposed" if j < 20 else "covered"
        k = j % 20
        if kind == "support":
            m = k < 14 if s == "exposed" else k < 2
        elif kind == "oppose":
            m = k < 2 if s == "exposed" else k < 14
        elif kind == "hold":
            m = k < 5
        else:
            m = False
        res_ = not m and k % 2 == 0
        claim = m or (k % 5 == 0 and (res_ or kind != "zero"))   # zero: claims exist but all resolved -> 0 mismatches
        rows.append(_row(f"t{j}", "fastapi" if k < 15 else "rich", s, "A_baseline", resolved=res_, claim=claim))
    if kind == "undet_empty":
        rows = [r for r in rows if r["stratum"] == "exposed"]
    return rows


def _syn_p2(kind):
    rows = []
    for j in range(60):
        repo = "fastapi" if j < 40 else "rich"
        a = j % 2 == 0
        if kind == "support":
            fail = (j % 10 < 9) if a else (j % 10 < 2)
        elif kind == "oppose":
            fail = (j % 10 < 2) if a else (j % 10 < 9)
        elif kind == "hold":
            fail = j % 10 < 5
        elif kind == "zero":           # A tasks exist, but no task fails -> outcome events 0 -> inconclusive
            fail = False
        else:
            fail, a = j % 10 < 5, False
        rows.append(_row(f"t{j}", repo, "exposed", "C_graphfirst", resolved=not fail, gold_A=False, anyA=a))
    return rows


def _traj(steps):
    """Minimal ATIF trajectory from (tool, args, response) and ('msg', text) tuples."""
    out = []
    for i, s in enumerate(steps, 1):
        if s[0] == "msg":
            out.append({"step_id": i, "source": "agent", "message": s[1], "extra": {"event_type": "text"}})
        else:
            name, args, resp = s
            out.append({"step_id": i, "source": "agent",
                        "tool_calls": [{"tool_call_id": f"c{i}", "function_name": name, "arguments": args}],
                        "observation": {"content": json.dumps(resp), "extra": {"tool_name": name}}})
    return {"schema_version": "ATIF-v1.7", "steps": out}


def selftest(argv):
    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(("PASS" if good else "FAIL"), name, "| got", got, "| want", want)

    # (1) four verdicts per hypothesis -- positive, negative, inconclusive, not decidable
    for kind, want in [("support", SUPPORT), ("oppose", OPPOSE), ("hold", HOLD), ("undet_noopp", UNDET),
                       ("undet_nolang", UNDET), ("zero", HOLD)]:
        chk(f"P1 {kind}", analyze_p1(_syn_p1(kind), "C_graphfirst")["verdict"], want)
    r0 = analyze_p1(_syn_p1("zero"), "C_graphfirst")
    chk("P1 zero: Wilson upper bounds reported", [round(r0["wilson1"][1], 3), round(r0["wilson0"][1], 3)],
        [round(wilson(0, 30)[1], 3)] * 2)
    chk("P1 zero: per-stratum opportunity", r0["opportunity_by_stratum"]["gold_event_and_utterance"], {"exposed": 30, "covered": 30})
    chk("P1 empty input", analyze_p1([], "C_graphfirst")["verdict"], UNDET)
    chk("P1 one stratum only", analyze_p1([r for r in _syn_p1("support") if r["stratum"] == "exposed"], "C_graphfirst")["verdict"], UNDET)
    for kind, want in [("support", SUPPORT), ("oppose", OPPOSE), ("hold", HOLD), ("zero", HOLD), ("undet", UNDET)]:
        chk(f"P2 {kind}", analyze_p2(_syn_p2(kind), "C_graphfirst")["verdict"], want)
    chk("P2 empty input", analyze_p2([], "C_graphfirst")["verdict"], UNDET)
    for kind, want in [("support", SUPPORT), ("oppose", OPPOSE), ("hold", HOLD), ("undet", UNDET)]:
        chk(f"P3 {kind}", analyze_p3(_syn_pairs(kind, "X"), "C_graphfirst", "D_guard_graphfirst")["verdict"], want)
    chk("P3 empty input", analyze_p3([], "C_graphfirst", "D_guard_graphfirst")["verdict"], UNDET)
    for kind, want in [("support", SUPPORT), ("oppose", OPPOSE), ("hold", HOLD), ("undet", UNDET)]:
        chk(f"P4 {kind}", analyze_p4(_syn_pairs(kind, "R"), "C_graphfirst", "D_guard_graphfirst")["verdict"], want)
    for kind, want in [("support", SUPPORT), ("oppose", OPPOSE), ("hold", HOLD), ("zero", HOLD), ("undet_empty", UNDET)]:
        chk(f"P5 {kind}", analyze_p5(_syn_p5(kind), "A_baseline")["verdict"], want)
    chk("P5 empty input", analyze_p5([], "A_baseline")["verdict"], UNDET)
    r5 = analyze_p5(_syn_p5("support"), "A_baseline")
    chk("P5 reports claim/unresolved rates + MH reference", [r5["claim_rate"]["exposed"] is not None,
        "rd" in r5["reference"]["repo_stratified_mh_rd"]], [True, True])
    chk("P1 condition isolation", analyze_p1([dict(r, cond="A_baseline") for r in _syn_p1("support")], "C_graphfirst")["verdict"], UNDET)
    full = analyze_rows([])
    chk("analyze_rows empty input -> all five not decidable", [full["primary"][k]["verdict"] for k in ["P1", "P2", "P3", "P4", "P5"]], [UNDET] * 5)
    # scale disagreement is flagged (audit case: 4/20 vs 0/27 fastapi, rich/requests zero)
    t = {"fastapi": (4, 20, 0, 27), "rich": (0, 23, 0, 5), "requests": (0, 4, 0, 2)}
    sr = _strat_result(t, {})
    chk("scale disagreement flagged (OR inconclusive, RD support)", [sr["verdict"], sr["rd_verdict"], sr["scale_agree"]],
        [HOLD, SUPPORT, False])
    # error rows: QA counts exit -1 even with empty error; P4 reference excludes them
    er = [_row("e1", "fastapi", "exposed", "C_graphfirst", exit_=-1), _row("e1", "fastapi", "exposed", "D_guard_graphfirst"),
          _row("e2", "fastapi", "exposed", "C_graphfirst"), _row("e2", "fastapi", "exposed", "D_guard_graphfirst", err="other")]
    chk("QA error rows = exit -1 or error", analyze_rows(er)["qa"]["error_rows_by_cond"],
        {"A_baseline": 0, "B_guard": 0, "C_graphfirst": 1, "D_guard_graphfirst": 1})
    chk("P4 reference excludes error rows", analyze_p4(er, "C_graphfirst", "D_guard_graphfirst")["reference"]["error_rows_excluded"]["pairs"], 0)

    # (2) numeric checks -- hand values and scipy
    chk("exact_mcnemar(0,6)", round(exact_mcnemar(0, 6), 6), round(2 / 64, 6))
    chk("exact_mcnemar(3,3)", exact_mcnemar(3, 3), 1.0)
    chk("wilson(0,10) upper", round(wilson(0, 10)[1], 4), 0.2775)
    d, ci = newcombe_unpaired(56, 70, 48, 80)        # Newcombe 1998, example (a): 0.2, [0.0524, 0.3339]
    chk("Newcombe unpaired example", [round(d, 4), round(ci[0], 4), round(ci[1], 4)], [0.2, 0.0524, 0.3339])
    d, ci = newcombe_paired(1, 2, 0, 1)
    d2, ci2 = newcombe_paired(1, 0, 2, 1)
    chk("Newcombe paired symmetry", [round(d + d2, 9), round(ci[0] + ci2[1], 9), round(ci[1] + ci2[0], 9)], [0.0, 0.0, 0.0])
    d, ci = newcombe_paired(5, 0, 0, 5)
    chk("Newcombe paired, identical arms", [d, ci[0] <= 0 <= ci[1]], [0.0, True])
    d, ci = newcombe_paired(0, 3, 3, 0)               # phi = -1 boundary: interval stays finite and contains 0
    chk("Newcombe paired, phi boundary", [d, ci[0] < 0 < ci[1]], [0.0, True])
    try:
        from scipy.stats import fisher_exact
        from scipy.stats.contingency import odds_ratio
        for tb in [(7, 10, 2, 10), (3, 12, 9, 15), (1, 5, 4, 4), (0, 6, 3, 7)]:
            x1, n1, x0, n0 = tb
            mtx = [[x1, n1 - x1], [x0, n0 - x0]]
            ex = exact_stratified([tb])
            orr = odds_ratio(mtx, kind="conditional")
            cil = orr.confidence_interval(0.95)
            got = [round(ex["p_upper"], 6), round(ex["p_lower"], 6), round(ex["or_cmle"], 4),
                   round(ex["or_ci95"][0], 4), (round(ex["or_ci95"][1], 3) if math.isfinite(ex["or_ci95"][1]) else "inf")]
            want = [round(float(fisher_exact(mtx, alternative="greater").pvalue), 6),
                    round(float(fisher_exact(mtx, alternative="less").pvalue), 6), round(float(orr.statistic), 4),
                    round(float(cil.low), 4), (round(float(cil.high), 3) if math.isfinite(cil.high) else "inf")]
            chk(f"single stratum exact test/CI = scipy {tb}", got, want)
    except ImportError:
        print("WARN scipy not available -- single-stratum scipy check skipped (hand checks only)")
    ex = exact_stratified([(2, 2, 0, 2), (2, 2, 0, 2)])
    chk("two strata by hand P(T>=4)=1/36", round(ex["p_upper"], 9), round(1 / 36, 9))
    chk("two strata upper CI inf at max T", math.isinf(ex["or_ci95"][1]), True)
    a1 = exact_stratified([(3, 8, 1, 9), (4, 6, 2, 7)])
    a2 = exact_stratified([(4, 6, 2, 7), (0, 5, 0, 5), (3, 8, 1, 9), (2, 2, 0, 0)])
    chk("invariant to stratum order and uninformative strata", [round(a1["p_upper"], 9), a1["informative_strata"]],
        [round(a2["p_upper"], 9), a2["informative_strata"]])
    for tb in [[(9, 10, 2, 10)], [(5, 10, 4, 10)], [(1, 10, 8, 10), (2, 6, 5, 6)]]:
        e = exact_stratified(tb)
        chk(f"CI excludes 1 <=> p < .05 {tb}", (e["or_ci95"][0] > 1 or e["or_ci95"][1] < 1), e["p_two_sided"] < ALPHA)

    # (3) readout layer
    te = load_te(_opt(argv, "--coder"))
    traj, _ = te._synthetic()
    m = task_measures(te, traj, {"serialize_response"})
    chk("readout: gold A_lang (positive)", [m["gold_events"], m["gold_A_lang"], m["gold_lang_opportunity"], m["recheck_mismatch"]], [1, True, 1, 0])
    m = task_measures(te, traj, {"solve_dependencies"})
    chk("readout: gold symbol grepped after empty (negative)", [m["gold_events"], m["gold_A_lang"]], [1, False])
    m = task_measures(te, traj, {"nothing_here"})
    chk("readout: no gold event", [m["gold_events"], m["gold_A_lang"], m["any_A_lang"], m["empty_then_X"], m["n_empty"]], [0, False, True, True, 2])
    # real qualnames from the sample (fastapi_14986, rich_3676) and a dunder gold
    chk("gold_names nested in method -> function before first <locals>",
        [sorted(gold_names(["FastAPI.setup.<locals>.openapi"])), sorted(gold_names(["Traceback.extract.<locals>.get_locals"]))],
        [["openapi", "setup"], ["extract", "get_locals"]])
    chk("gold_names misc", sorted(gold_names(["APIRoute.__init__", "get_request_handler.<locals>.app", "Dependant.cache_key", "solve"])),
        sorted(["APIRoute", "app", "get_request_handler", "cache_key", "solve"]))
    chk("gold_names strict", sorted(gold_names(["APIRoute.__init__", "FastAPI.setup.<locals>.openapi", "solve"], strict=True)),
        ["openapi", "solve"])
    chk("event_names dunder query -> owner", [sorted(event_names(te, "fastapi.routing.APIRoute.__init__")),
                                              sorted(event_names(te, "APIRoute.__init__")),
                                              sorted(event_names(te, "def __init__(self, path):"))],
        [["APIRoute", "__init__"], ["APIRoute", "__init__"], ["__init__"]])
    tj = _traj([("get_code_neighbors", {"node": "fastapi.routing.APIRoute.__init__"}, {"status": "ok", "neighbors": [], "count": 0}),
                ("msg", "The graph returned no neighbors, so APIRoute.__init__ does not exist in this codebase."),
                ("read_file", {"filepath": "fastapi/routing.py"}, {"status": "ok", "content": "..."})])
    m = task_measures(te, tj, gold_names(["APIRoute.__init__"]), gold_names(["APIRoute.__init__"], strict=True))
    chk("readout: APIRoute.__init__ query counts as a gold event (expanded), not strict",
        [m["gold_events"], m["gold_A_lang"], m["gold_A_lang_empty"], m["gold_events_strict"], m["recheck_mismatch"], len(m["gold_hits"])],
        [1, True, True, 0, 0, 1])

    # (4) real data: window re-implementation vs 0.2 (prints mismatch count only)
    runs = [p for p in argv if Path(os.path.expanduser(p)).exists()]
    if runs:
        n_ev = bad = 0
        for run in runs:
            for c in CONDS:
                for tf in sorted((Path(os.path.expanduser(run)) / c / "traces").glob("trace_*.json")):
                    mm = task_measures(te, json.load(open(tf)), set())
                    n_ev += mm["n_graph_events"]
                    bad += mm["recheck_mismatch"]
        chk("real data: re-implemented window A_lang = 0.2 A_lang (mismatch count)", bad, 0)
        chk("real data: events were actually read (nonzero)", n_ev > 0, True)
    print("SELFTEST", "PASS" if ok else "FAIL", "analysis", ANALYSIS_VERSION)
    return ok


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "build":
        build(rest)
    elif cmd == "analyze":
        analyze(rest)
    elif cmd == "selftest":
        return 0 if selftest(rest) else 1
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
