> English translation of the Korean pre-registration. The Korean original is the binding text; its SHA-256 is e6756e3fb1470988974e6ecfbcba38d4a7b8b6280afb5b8ae8dca99ffb3b9565. Translation made on 2026-11-08; where the translation and the original differ, the original governs.

# Gemma4Paper · Part 2 analysis pre-registration

> Written on the night of 2026-10-05, **before seeing the first Part 2 trajectories (v3 smoke test)**. What this document fixes is not changed after the main run —
> if something must change, it is not deleted but appended to the "Change log" with the date and reason, and disclosed in the manuscript as "a deviation from the pre-registration".
> Basis of the decisions: internal decision log 2026-10-05 "pre-emption by competition discussion" (Part 2 re-centred) · "exposure definition a∪b".
> Where this goes in the manuscript: outline §5.1–§5.5. The public notebook carries an English summary of this document and the commit hash (Verifiability).

## 0. Freeze status

| Item | Value | Status |
|---|---|---|
| Judge | `coder/trace_events.py` RULES_VERSION `0.2` · blob `7ad46b9e` · freeze commit `93a0eb78` (10-07) | ✅ Frozen. Event definitions are not changed afterwards — only parsing-defect fixes raise the version to `0.2.x` and are recorded in the change log |
| Primary window k | **3** (shared by A_lang and X, code `K_DEFAULT = 3`) | ✅ Author's decision on the night of 10-05, before seeing the v3 trajectories |
| Stratum table | `[internal path]/derived/part2_strata.tsv` (strict 109) · exposed 47 · covered 34 · unobserved 28 | ✅ Frozen (exposure definition a∪b, author's decision 10-05) |
| Bundles | `bundles/A_baseline` · `bundles/B_guard` (the only difference is the guard block + the skill `empty-result-check`) | ✅ Frozen. B was submitted to the main competition on 10-05 (ref 56854337, zip sha256 `a2a67657…`) |
| Harness | competition wheelhouse, 09-30 version (swegemma 0.2.7 — the version string is unchanged, so it is recorded by sha256) · default budget per task 60 minutes · 100 tool calls · 300 seconds per command | used as-is by the kernel (`kernel/gemma4paper_part2.py`; in this release the defaults are on lines 215–216) |

🔴 **The v3 smoke-test trajectories (fastapi_11194 · rich_3061 · requests_6757, A × 3) are excluded from the confirmatory analysis.** The only thing those trajectories may be used for is
fixing *parsing defects* of the judge (failure to read a format · empty strings); the event *definitions* (what counts as an absence conclusion) are not changed.
If fixing a parsing defect raises the version, the same trajectories are re-run together with the selftest and the difference is recorded.

## 1. Questions and hypotheses

The exposure variable fixed by Part 1 (independent replication · gaps conditional on the reference) is used as the axis of Part 2. The task unit is primary.

| | Hypothesis | Primary measure | Decision rule |
|---|---|---|---|
| P1 | In exposed tasks the agent more often reaches an absence conclusion about the reference function | task-level A_lang (reference-function symbol, condition A) — exposed vs. covered | repository-stratified exact test (exact Mantel–Haenszel, or Fisher combined across repositories). If the 95% interval of the difference is above 0, supported; below 0, opposed; containing 0, inconclusive |
| P2 | Tasks with an absence conclusion have more verification failures | P(V \| A) − P(V \| ¬A), task level | same rule |
| P3 | The guard (B) increases grep cross-checks after empty results (manipulation check) | task level "was there at least one X within k after E_empty", A vs. B paired | exact McNemar, discordant pairs b·c reported as they are |
| P4 | The guard does not lower the resolution rate | resolution rate B − A, paired | **non-inferiority statement only** — report the interval; write "improved" only when the interval is above 0 |
| P5 | Self-report disagreement (S_claim but FAIL) concentrates in exposed tasks | disagreement rate exposed vs. covered | report by interval only |

- Opposing prediction (manuscript §2): CodeAnchor and ARISE hold that empty structural information does not change behaviour. If P1 and P2 come out inconclusive or opposed, **we report that as a replication of theirs** — negative results go in the same table.
- 🔴 The reason P4 is not primary is the power in §3. Even running all 109 tasks in pairs gives no power to detect a difference in resolution rate.
- The 28 unobserved tasks are not included in the comparison and are described separately (no incoming edge to the reference was observed, so exposure cannot be determined).

## 2. Event definitions and k

The canonical definitions are in `coder/trace_events.py` (same as manuscript §5.2): E_empty · E_error · E_unparsed · A_lang · A_beh · X · S_claim.

- The primary outcome is A_lang. A_beh only decreases monotonically as k grows, so choosing one k fixes its value — therefore **for A_beh the whole curve over k ∈ {1, 2, 3, 5, 8} is reported**, and it is not used for the primary verdict.
- Primary k (shared by A_lang and X): **3** — author's decision (night of 10-05, before seeing the v3 trajectories). RULES_VERSION is raised to `0.2` and frozen after the definition question below is settled.
- One definition question is open: whether a `run_command` whose reproduction-script arguments contain the symbol string counts as "searched again (not X, A_beh resolved)". [Decision needed — ask the author after seeing the first case in the v3 trajectories]. Once decided, it is not changed.
- Judging is rule-based and local only (competition data are not sent to external APIs). The author hand-labels a stratified sample of [N_judge] items and reports the agreement rate with a Wilson interval.

## 3. Power (computed before running, night of 10-05)

Exact-test simulation (2,000 runs, seed 20261005, `probes/part2_power.py` — moved into the public notebook).

Exposed vs. covered, one run per task, one-sided Fisher α = .05, minimum difference (percentage points) reaching power .8:

| Sample | baseline p0 = .1 | .2 | .3 | .5 |
|---|---:|---:|---:|---:|
| All 47 vs. 34 | 25 | 29 | 31 | 29 |
| fastapi 20 vs. 27 | 37 | 38 | 40 | 37 |
| rich 23 vs. 5 | 65 | 66 | 64 | — |

Power of the paired McNemar test (two-sided α = .05) for A vs. B resolution rate — b = probability only B resolves, c = probability only A resolves:

| Tasks | b .10 · c .03 | b .08 · c .04 | b .06 · c .03 | b .15 · c .05 |
|---:|---:|---:|---:|---:|
| 40 | .09 | .04 | .01 | .18 |
| 81 | .31 | .10 | .07 | .45 |
| 109 | .44 | .14 | .10 | .59 |

How to read this:

- P1 and P2 can detect **only differences of about 30 percentage points or more**. Given the size of the Part 1 gaps (61.1% of tasks with zero incoming edges to the reference), a difference of that size could appear if exposure changes behaviour, but small effects are written only as "the interval contains 0".
- rich has only 5 covered tasks, so a within-repository comparison is impossible. The information in the repository-stratified test comes almost entirely from fastapi — this is stated as is in the manuscript.
- P4 (resolution rate) does not exceed power .6 at any realistic sample size → kept as a non-inferiority statement (§1). Repeats per task only reduce within-task variance; they do not increase the number of tasks.
- P3 (manipulation check) is expected to show a large effect if the guard works (the prompt directly instructs grep). This is the primary evidence for "did the guard change behaviour".

## 4. Sample and run order

- Target: exposed 47 + covered 34 = 81 tasks (within the strict 109). The run order has **already been drawn** as a random permutation (seed 20261005, `probes/part2_order.py`) — `[internal path]/derived/part2_order.tsv` (first 16 hex of sha256 `5ee35d4950425d2c`, first five fastapi_13786 · fastapi_13920 · requests_7433 · fastapi_14419 · fastapi_14978). If quota runs short, the list is cut **from the front of that permutation** — no selection after seeing results.
- Conditions: A and B paired on the same task. Repeat r = 1 is first run on all 81 tasks; if quota remains, r = 2 is added in the same permutation.
- Quota (`kaggle quota`, night of 10-05): 30h/week, L4×4 is charged double → 15h/week of wall time. Until the experiment freeze on 11-01, about 4 weeks ≈ 60h of wall time. One kernel run ≤ 12h, vLLM start-up about 20 minutes. The mean time per task t is measured with v3 — at t = 10 minutes, about 360 task-condition runs (81 × 2 conditions × 2 repeats ≈ 324).
- 🔴 The smoke-test task `requests_6757` is outside the strict 109.

### 4-1. Auxiliary arm — proxy Gemma 4 31B (added by author's decision on 10-06, before confirmatory runs)

- What: the same harness, the same bundles (A and B), the same 81 tasks and the same permutation are run with `google/gemma-4-31b` through the Kaggle Benchmarks Model Proxy. This is not the competition model (`gemma-4-31b-it-qat-w4a16-ct`, self-served with vLLM) — the serving precision and inference settings on the proxy side are not public.
- Status: **reported only as an exploratory result.** P1–P5 verdicts are made only from the main arm (L4 kernel). The auxiliary arm goes in a separate table, noting only whether its direction matches the main arm. If the main arm is cut by quota, the auxiliary arm's 81-task results are disclosed separately as "tasks the main arm did not see" (not a substitute for the main arm).
- Measures: event counts, A_lang and resolution rate with the same definitions as the main arm (§2, same judge version, k = 3). In addition, the graph-tool call rate is placed beside the main arm's — to tell whether non-use of the graph is due to the model serving side.
- Execution: runs only inside the task runtime (competition data do not leave Kaggle). 🔴 Competition data are sent only to Gemma (author's condition) — a guard at the top of the task function stops before touching the data if the model is not Gemma. Since it uses no GPU quota, r = 1 is run for all 81 × 2, from the front of the permutation.
- Basis of feasibility: the 10-06 probe (pilot task requests_7315, one A run) completed — unresolved, 28 tool calls, 165 seconds, 0 graph calls. This one run is a pilot and is not included in the analysis.

## 5. Hidden-set submissions to the main competition (auxiliary)

- The main competition allows one submission a day, and the hidden set is graded in the host's sandbox (same graph-generation method, `spec/main_data_description.md` line 7). Only a single score comes back, no trajectories.
- The purpose is an auxiliary check of "is the direction on the public set the same on the hidden set". The resolution is low (one task ≈ 0.017), so it is not used as evidence of effect size.
- Record: B 10-05 (ref 56854337) · A 10-06 (ref 56864469). A is the same text as the public baseline (Rozen V1, Public LB 0.12), but is submitted the next day to match the grading conditions of the same period.

## 6. Reporting commitments

- All of P1–P5 go in one table with their verdicts (supported · opposed · inconclusive).
- The numbers in the manuscript are filled from the single `results.json` produced by the script.
- Changes after this document are appended below.

## Change log

- Night of 10-05 (before running): primary k = 3 confirmed (author). Not a definition change — fills the [Decision needed] in §0 and §2.
- 10-06 (observation only, no definition change): in the v3 smoke test, A × 3 runs, 0 graph-tool calls → 0 events. 106–473 seconds per task, vLLM start-up about 12 minutes. Whether to change the design awaits the author's decision — if changed, it is written below this line.
- 10-06 (not a design change — pilot added): by author's decision, a **confirmation pilot v4** is run outside the confirmatory sample of 81 (from the 28 unobserved). Per-repository draw (seed 20261006) fastapi_14953 · 14372 · 15588 · 14492 · 15661 · rich_3777 · 3105 · 4077 · 3938 · requests_7315, 10 each for A and B. Purpose: the graph-tool call rate. If the design is changed because of the pilot results (e.g. a graph-forcing condition), it is written below **before running the confirmatory sample of 81**. Pilot trajectories are not included in the confirmatory analysis.
- 10-06 14:50 (design addition — before confirmatory runs, no change to the main-arm definitions): by author's decision, **the §4-1 auxiliary arm (proxy Gemma 4 31B)** was added. Reported only as an exploratory result and not used for P1–P5 verdicts.
- Night of 10-06 (**design change — before confirmatory runs**, after seeing the pilot v4 results): by author's decision, **condition C (`bundles/C_graphfirst`)** is added.
  - Trigger: in the v4 pilot (A and B × 10, L4 · competition model) the graph tools were called **2 times in 20 runs** (A: fastapi_14953 `search_similar_code` 1 · rich_4077 `get_code_neighbors` 1, B: 0). Same direction as v3's 3 runs with 0 calls and the proxy probe's 0 calls. In A, E_empty hardly occurs, so P1 is undefined.
  - Definition of C: differs from A only by one "Graph first (required)" block in `prompts/analyzer.md` — the analyzer calls `search_similar_code` and `get_code_neighbors` (and `get_code_subgraph` if needed) with the issue's identifiers before the first `run_command`. **It says nothing about how to read empty results** (that is B's treatment). Passed the format check `adk_submission.validate_directory` (on a local workstation).
  - Measure moved: **P1 is measured in condition C** (exposed vs. covered, decision rule unchanged). "The baseline does not call the graph" (A's graph call rate) is reported from A as a **new descriptive result** — a proportion and interval, not a hypothesis test.
  - P3 (guard manipulation check) stays A vs. B. ⚠️ If both A and B hardly call the graph and E_empty is rare, P3 is also undefined — then it is reported as "not definable (event count n)". D (= B + Graph first), which tests the guard on top of graph forcing, was not included in this change (open, author's decision).
  - Sample, order, k and judge definitions are not changed. 81 × 3 conditions at r = 1 is about 38h, within the quota before the paper deadline (11-12 UTC). Pilot v4 trajectories are not included in the confirmatory analysis.
- Night of 10-06 (**design change — before confirmatory runs**, continuing the item just above): by author's decision, **condition D (`bundles/D_guard_graphfirst`) = B + the same "Graph first" block (in the same place as C)** is added. The difference between D and C is the same as between B and A (two guard blocks + the skill) (checked by diff).
  - Measure moved: **P3 (guard manipulation check) and P4 (non-inferiority) are measured as D vs. C pairs** — the guard is tested on a condition where the graph is actually called. A vs. B reports the same measures as auxiliary (if there are no events, "not definable (n)").
  - 81 × 4 conditions at r = 1 ≈ 50h, within quota before the paper deadline. Passed the format check (on a local workstation) · C and D added to the bundle dataset.
  - Smoke test v5 before confirmatory runs: C and D × 2 tasks (fastapi_14953 · rich_4077 — tasks on which A called the graph once in pilot v4, outside the confirmatory sample). Purpose: whether the "Graph first" block actually produces graph calls (manipulation check). Not included in the confirmatory analysis.
- 10-07 03:00 (**§4-1 auxiliary arm stopped** — no change to the main-arm definitions): author's decision. Only s1 and s2 (9 tasks each × A and B, proxy google/gemma-4-31b) are run; s3–s9 are not.
  - Basis: in 36 runs, 0 resolved · 1 graph call (s1 B). The `error` field newly added in s2 confirmed that the cause of exit -1 is a **proxy empty response** (content and tool_calls None, usage 0 tokens — the harness discards even the patch to be submitted on that exception) (s2 5/18, B 4 · A 1). This failure does not exist in competition grading (local vLLM on L4) and contaminates the auxiliary arm's comparison. The L4 exit -1 (v4) has a different cause (ContextWindowExceeded).
  - Reporting: only "proxy arm 18 tasks × 2, 0/36 resolved, 1/36 graph calls, number of rows whose patch was lost to a proxy empty response" is reported as an exploratory result. ⚠️ The `n_error` in the s2 summary line changed meaning because every row got an `error` key — count by the row's `error` value.
  - Outputs `[internal path]/runs/aux_s1_20261006/` · `aux_s2_20261006/`.
- 10-07 09:00 (no definition change — run record): smoke test v5 (C and D × fastapi_14953 · rich_4077) **passed the manipulation check** — all 4 runs called the graph (C 8 · 1, D 3 · 2), E_empty 13 · E_full_untraced 1 (judge 0.2-draft). Confirmatory round 1 v6 = the first 16 tasks of the permutation × A, B, C, D was pushed (author's decision). The kernel loop was changed to tasks outside and conditions inside, so condition pairs are not broken even at the time limit.
- 10-07 judge 0.2 frozen (commit `93a0eb78`): the remaining definition, "symbols in the arguments of reproduction scripts and test runs", is counted as **searched again** (A_beh resolved) (author's decision). Code behaviour is the same as 0.2-draft (only documentation and the version string changed). ⚠️ Honest timing record — the freeze came about 30 minutes **after** the v6 push, but **before reading a single line** of v6 output.
- 10-07 13:00 (no definition change — run record): v6 complete, 16 tasks × 4 conditions, 64 rows, none missing. Only a readout (descriptive statistics for progress, `coder/run_readout.py`) was produced; the P1–P4 tests are deferred until all tasks are done. 🔴 Correction of the sample plan: a 4×L4 kernel charges quota per GPU (run 4.17h → quota +15.9h) — "81 × 4 ≈ 50h" (the 10-06 item above) was wrong; measured ≈ 1.0h per task, 81 tasks ≈ 81h. This fits within five weekly refreshes before the paper deadline (11-13). Order and definitions are unchanged.
- **Evening of 2026-10-10 — auxiliary arm "0.2.11 · thinking recorded" added (author's decision, before seeing auxiliary-arm data).** At the mid-point check of 32 tasks in the main experiment, A_lang was 0 of 166 E_empty events, and a positive control confirmed that the cause was not "a detector defect" but "only 10/166 events have any message in the window after them — in 0.2.7 thinking is off, so the language channel barely exists" (internal mid-point review document §6). The main experiment's P1 definition and decision rule are not changed (left as is, it becomes "not decidable for lack of event opportunity"). Auxiliary arm: the harness wheelhouse of 10-09 (swegemma 0.2.11 · adk_submission 0.2.13, thinking on) + a copy of bundle C with only `include_thoughts` set to true (with false, 0.2.13 strips thought parts from the response — `adk_submission/resolvers/generation.py` `_strip_thought_parts_from_response`). Kernel `kernel_aux0211/`. Stage 1 smoke test = one task, fastapi_13786, to see whether messages appear in the trajectory (`### AUXMSG`). If they do, stage 2 = v6 permutation positions 1–16 × C′. The judge stays 0.2, and thought text also counts as a "message" for A_lang. Because this arm differs from the main experiment in three things — harness version, prompt and thought recording — it is reported **only as a descriptive result, not as P1 confirmation** (0.2.11 resolves short names to other nodes, so E_empty itself decreases — impact analysis §3).

### Change log 2026-10-11: A_lang broadened-lexicon sensitivity (exploratory, main analysis unchanged)

- In auxiliary v3 (thinking on), the 0.2 ABSENCE lexicon missed messages like "`TypeAlias` didn't return anything" right after E_empty (A_lang 0/3).
- The main analysis stays the frozen 0.2. Judging with a broadened lexicon (`coder/a_lang_sensitivity.py`) was built after seeing the results, so it is reported only as an exploratory sensitivity: auxiliary 2/3, main experiment 0/186 (unchanged because there is no language channel).
- The judge's miss itself is written into the manuscript as a limitation and a finding. Author's decision 2026-10-11.

### Change log 2026-10-11 (recorded retroactively): 10-10 harness pin · P2 not decidable

- Retroactive record — the 10-10 decision (internal decision log "2026-10-10 Gemma4Paper round 2 harness = pinned to the old version 0.2.7 + 0.2.11 reported at the tool layer") was missing from this document (pointed out in the 10-11 mock review, W3). After the host changed the 10-09 wheelhouse to 0.2.11, v8 and v9 ran on swegemma 0.2.7 · adk_submission 0.2.12 pinned in a private dataset. At the time of the decision, confirmatory output for 16 tasks (v6) had been seen.
- P2's A is the primary outcome A_lang, so if A_lang is 0, P2 is also not decidable. This is not a definition change but a record of a consequence of the decision rule.
- Attribution of thinking being off: what turned thinking off in 0.2.12 is the `include_thoughts: false` setting common to all four bundles (not an inherent property of the harness). Manuscript §5.2b and §6.3 corrected (10-11).

### Change log 2026-10-12: P1–P5 confirmatory analysis script fixed (points the pre-registration did not settle)

- What: the points this document did not settle uniquely were settled by the analysis script confirm_p1p5.py (analysis 1.1,
  sha256 ae726b5fe004281ccbf083878ff33c723a29d321096a7ab2e6f1459dc8d08071). The hash scope is MANIFEST.txt
  (sha256 0e47607b2d56642e514f4908966f33fbd6bcc4e7a12be495f123095f21d98150), which also binds the sha256 of the inputs that determine the verdicts:
  trace_events.py (0.2, git blob 7ad46b9e) · gold_vs_graph.json · part2_order.tsv · part2_strata.tsv.
  At the point of 39/81 tasks in the main experiment, permutation positions 40 onward not yet run. Judge 0.2, k = 3, sample and order were not changed.
  This is the version fixed after an internal audit (1.0 → 1.1); 1.0 was not published.
- What was seen before fixing: the progress readout (coder/run_readout.py, descriptive statistics) of per-condition resolution · graph calls · E_empty · tasks with a cross-check after E_empty ·
  S_claim unresolved · condition-pair resolution discordance (printed by the script; includes the C vs. D discordant pairs = P4's b·c), and in manuscript §5.2b, after E_empty,
  A_lang 0/186 · message within the window 10/166. After running 1.0 on the interim data, a sample-check block (rows per condition · missing trajectories · permutation prefix ·
  error rows per condition) was printed to the screen once.
  Not seen: any split by exposure stratum, any P1–P5 test value or interval. The result file from running this script on the interim data was not opened until the hash of the fixed version was published.
- What was settled:
  1. Condition: P2 uses P1's outcome (A_lang) as its explanatory variable, so it uses the same C as P1. P5 does not use graph events and so was not subject to the 10-06 move, so it uses
     the original baseline A. The same values in other conditions go in an auxiliary table without verdicts. The interpretation of P5 (A) is restricted to "a correlation in a condition where the graph path is closed".
     In the auxiliary P2, B and D raise A_lang when the agent repeats the guard text (empty results are "UNCONFIRMED, not 'does not exist'"), so this is not read as an absence conclusion.
  2. Scale: "the 95% interval of the difference" is judged by the exact 95% interval of the common odds ratio produced by the named test (exact Mantel–Haenszel = repository-stratified exact conditional test)
     (Fisher combination does not produce an interval). The MH risk difference and Sato interval are reported alongside, and if the verdicts on the two scales disagree,
     that fact is noted in the table (rd_verdict · scale_agree). Two-sided p = 2 × min(one-sided) (may differ from the two-sided p of R's mantelhaen.test).
     The power in §3 was computed one-sided at .05, so the minimum detectable difference for the actual verdict (two-sided 95%) is larger than in the table.
     For P2 the primary measure is a difference, so the risk difference is reported as the first number.
  3. Not decidable: used only when the estimator has no denominator (0 judgeable tasks · 0 in one group · 0 tasks with A_lang for P2 · 0 eligible pairs for P3 · 0 pairs for P4) and for
     "absence of event opportunity" in the 10-10 record (P1: no task has a graph event on the reference function, or no message at all in the window after such events).
     If there is opportunity but 0 outcome events, it is inconclusive by the interval rule, with per-stratum opportunity counts and Wilson upper bounds, following the §1 commitment to report opposing predictions.
  4. P3: z is defined only in tasks with E_empty, so the test uses pairs where both conditions have E_empty. The version putting tasks without E_empty in as z = 0 is
     a reference row. Verdict mapping (not in the §1 table): exact McNemar two-sided p < .05 and b > c, supported; c > b, opposed; otherwise inconclusive.
     P4 and P5 fill "all with verdicts" in §6 by mapping intervals to verdicts (lower bound > 0 supported · upper bound < 0 opposed · otherwise inconclusive). P4 has no margin, so
     it is not written as "non-inferior".
  5. Reference-function symbols: for each function · class · async · nested qualname in gold_vs_graph.json, the last identifier. If the last is a dunder, the owning class;
     if nested, also the function just before the first <locals>. The same transform on the graph-event side (if the last component of a dotted query is a dunder, the preceding component). The version without the expansion is a reference row.
     Reference events in which an absence sentence was detected are split out per task (p1_hits.jsonl) and passed to hand labelling — the verdict is the automatic count as is.
  6. P1 denominator: all tasks in the stratum (§3 "47 vs. 34"). Tasks with no reference event have y = 0. Events of any kind, all graph responses (judge
     A_lang definition). Per-stratum opportunity counts are reported alongside, and the opportunity-conditional version and the E_empty-only version are given as reference rows.
  7. Run-error rows (exit −1 or error) are not excluded and the harness's resolved is used (P2 and P4 excluding error rows are reference rows; for P2, error-row counts per A/¬A group).
     r ≥ 2 is excluded from the primary analysis and only counted — even if collected for all 81 tasks, it is used only as auxiliary.
  8. P5 denominator: all tasks in the stratum ("concentrates" = per-stratum incidence). Per-stratum claim rates and unresolved rates are reported side by side; the S_claim-conditional version and the repository-stratified version (MH risk difference) are reference rows.
  9. The task-level outcome is "any of its events" (same rule as the P3 wording). The manuscript §5.4 wording "first event per task" (10-03, before this document) is to be corrected.


- Manuscript Table 3 row and text for the places to fix in the manuscript: an internal note, sections "Manuscript Table 3" and "Places to fix together in the manuscript" (manuscript update is the next task).
- Hash publication (author's decision "Kaggle private notebook"): `earthmaker/gemma4paper-confirm-p1p5-commit` version 1, run completed 2026-10-12 07:07:31 UTC
  (after the MANIFEST fix at 07:02:55Z). The notebook restored MANIFEST.txt · confirm_p1p5.py · selftest.log from base64 and printed their sha256;
  all three matched the values above (selftest.log 5f5d4f98193b81c39626b69be969d89897bcdea50a1b40b65245d6ee7b3ad4f4). No data, GPU or internet.
  Being private, the evidence of timing is the Kaggle version history. Making it public at manuscript submission lets third parties check it.

## Translator's notes

Places where the translation replaces internal detail with a neutral expression (contents not given):

- Internal file paths replaced by "[internal path]": 3
- Internal machine names replaced by "a local workstation": 2
- References to the internal decision log, given as "internal decision log" without its file name: 2
- File name of an internal review document replaced by "internal mid-point review document": 1
- "User's decision" rendered as "author's decision" throughout (the author is the person who made these decisions).
- The title drops an internal folder prefix, and one internal note is referred to as "an internal note" (its path and file name are omitted).
- The kernel line reference in §0 is updated to this release; the original cites the line numbers of the internal copy.
