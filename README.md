# When count: 0 Means "Not Indexed": code and pre-registration

Code, agent bundles and the frozen analysis for the Kaggle writeup ["When count: 0 Means "Not Indexed": Code-Graph Gaps and a 4-bit Gemma 4 Agent"](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/writeups/when-count-0-means-not-indexed-code-graph-gaps) (Google - The Gemma 4 Developer Agent Paper Track).

Competition data (repository snapshots, call graphs, embeddings, `tasks.jsonl`, patches) are not redistributed here. Scripts that need them read the competition dataset from paths you set (see "Paths").

## Layout

| Folder | Contents | Paper section |
|---|---|---|
| `probes/probe_empty.py` | Interface probe on a synthetic graph: shows that a missing symbol, a mis-specified argument and a truly empty neighbourhood all return `ok` with zero results. Needs the public harness wheel, no competition data. | §3 |
| `probes/` (other files) | Part 1: reference-edit functions, runtime call edges collected while the tests run, recall of the static graph against them, and the per-task statistics. | §4 |
| `bundles/` | The four agent configurations: A (public baseline used as is), B (A plus the empty-answer guard), C (A plus the graph-first block), D (B plus the graph-first block). | §5.1 |
| `kernel/` | Kaggle notebook that runs the bundles on the public tasks (L4 x4) and keeps the traces; `aux/` holds its helper scripts. | §5.1 |
| `coder/trace_events.py` | Rule-based event judge, version 0.2, frozen before any confirmatory output was read. | §5.2 |
| `coder/run_readout.py` | Descriptive progress readout used during the runs (no tests). | §5.5 |
| `coder/frozen/` | Frozen confirmatory analysis for P1-P5 (`confirm_p1p5.py`), its self-test log and `MANIFEST.txt`. | §5.4 |
| `coder/scripts/` | The exact commands of the 81-task analysis, plus the descriptive and exploratory measures. | §5.5 |
| `coder/a_lang_sensitivity.py` | Exploratory broadened absence lexicon. | §5.3 |
| `SUPPLEMENT.md` | Values the paper cites but does not print: per-repository recall, the plan changes, the cause-labelling rule sets, two definitions of reference-edit queries, and the pre-registered auxiliary rows. | §4–§5 |
| `PREREGISTRATION_en.md` | English translation of the pre-registration. The Korean original is the binding text; its SHA-256 is given at the top of the translation. | §5 |

Not included: the three derived data files listed in `MANIFEST.txt` (`gold_vs_graph.json`, `part2_order.tsv`, `part2_strata.tsv`), which are built from competition data, and two items the pre-registration mentions: the competition's own data description (`spec/main_data_description.md`), which belongs to the competition materials, and the notebook folder of the exploratory auxiliary arm (`kernel_aux0211/`).

## Hashes posted before release

On 1 November 2026 we posted these SHA-256 values to the Paper Track forum ([topic 754667](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/754667)). The post also states that the final 81-task results had been opened on 24 October, before the hashes were posted.

```
0e47607b2d56642e514f4908966f33fbd6bcc4e7a12be495f123095f21d98150  coder/frozen/MANIFEST.txt
ae726b5fe004281ccbf083878ff33c723a29d321096a7ab2e6f1459dc8d08071  coder/frozen/confirm_p1p5.py
5f5d4f98193b81c39626b69be969d89897bcdea50a1b40b65245d6ee7b3ad4f4  coder/frozen/selftest.log
376bdbb4c9cf8925c080e96afa780fce72e2c720ec35caa88d820d86d29cf5ce  coder/trace_events.py
```

These four files are released byte for byte, which is why `coder/trace_events.py` and `coder/frozen/confirm_p1p5.py` keep their original Korean comments.

Check with `shasum -a 256 <file>` (macOS) or `sha256sum <file>` (Linux). `python3 coder/frozen/confirm_p1p5.py selftest --coder coder` runs the synthetic controls and numeric checks of `selftest.log` and ends with `SELFTEST PASS analysis 1.1`. Two checks in the log, the two lines just before that final line, read real run outputs and are skipped unless the run folders are given as arguments. `python3 coder/trace_events.py --selftest` checks the judge and ends with `SELFTEST PASS 0.2`.

### Known documentation mismatches in the hashed files

The hashed files cannot be edited, so mismatches between their comments and their code are listed here. None of them changes a result.

- `coder/trace_events.py`: the usage line lists `--task <tasks.jsonl>`, which `main()` does not read (only `--rt` and `--k`). The `E_incomplete` rule also skips responses marked `is_truncated`. The cross-check regex matches `egrep`, `fgrep`, `ack` and `ag` as well as the listed `grep`, `rg`, `find` and `git grep`. The failed-test pattern also matches any `Traceback`, any line starting with `ERROR ` and any `^FAILED ` line. When no pending call has the same tool name, a response is paired with the oldest pending call of any tool.
- `coder/frozen/confirm_p1p5.py`: the docstring cites the Korean pre-registration by its internal file name; its translation is `PREREGISTRATION_en.md`.

## Paths

Scripts read their inputs from environment variables. Only `G4` is required; the others have the defaults shown.

| Variable | Default | Read by | Meaning |
|---|---|---|---|
| `G4` | none (required) | `probes/gold_check.py`, `gold_vs_graph.py`, `rt_vs_graph.py`, `part1_stats.py`, `audit_prep.py` | Part 1 work folder holding `part/` (with `tasks.jsonl`), `full/` (with `graphs/`), `rt_out/` and `rt_out_gold/` |
| `G4P_DATA` | `data` | `probes/issue_symbols.py`, `r7b.py`, `snippet_probe.py` | competition dataset root |
| `G4P_DERIVED` | `derived` | `probes/part2_order.py` (writes `part2_order.tsv`), `kernel/aux/make_shards.py`, `coder/scripts/run_all_1024.sh` | derived tables |
| `G4P_AUDIT` | `audit` | `probes/audit_prep.py` | audit samples |
| `G4P_WORK` | `.` | `coder/scripts/assemble_check.py`, `probes/cmp745731.py` | root that must contain `derived/part2_order.tsv` and `runs/<run>/out/` (`assemble_check.py`) or `data/tasks.jsonl` (`cmp745731.py`); these two scripts do not read `G4P_DERIVED`, `G4P_RUNS` or `G4P_DATA` |
| `G4P_RUNS` | `runs` | `coder/scripts/run_all_1024.sh` | Part 2 run outputs, one folder per run: `v6_confirm1`, `v8_confirm2`, `v9_confirm3`, `v10_confirm4`, `v11_confirm5`, each with `out/` |
| `G4P_CODER` | the `coder/` folder | `coder/scripts/run_all_1024.sh` | this repository's `coder/` folder |

`coder/scripts/run_all_1024.sh` takes the frozen folder and an output folder as arguments; because `assemble_check.py` reads `G4P_WORK`, run it from a folder that has `derived/` and `runs/`, or set `G4P_WORK` to one.

Other scripts:

- `probes/rt_batch.py` uses a fixed work folder `~/gemma4paper` (with `data/` and a Python 3.13 environment `rt313/`), and reads `MODE` (`base` or `gold`, default `base`) and `NJ` (parallel jobs, default 6). It runs the tests with `probes/rt_callgraph.py` as a pytest plugin, passing `RT_ROOT` (repository root) and `RT_OUT` (output file).
- `kernel/aux/` scripts run inside Kaggle notebooks and read the notebook's environment (`MODEL_PROXY_URL`, `MODEL_PROXY_API_KEY`, `KAGGLE_API_TOKEN` and their own `AUX_*` or `PROBE_*` settings).

Harness: swegemma 0.2.7 from the competition wheelhouse of 30 September 2026 (wheel SHA-256 in the paper, §7). `probes/probe_empty.py` also needs `adk_eval_core` from the same wheelhouse.

## Attribution and license

Bundle A is the public baseline by Roman Rozen ([notebook](https://www.kaggle.com/code/romanrozen/gemma-eda-baseline-for-a-start-lb-top-1), version 1), used under the Apache License 2.0; bundles B, C and D modify its prompts. See `NOTICE`.

Code and bundles: Apache License 2.0 (`LICENSE`). Documentation, including this README, `SUPPLEMENT.md` and `PREREGISTRATION_en.md`: CC BY 4.0 (`LICENSE-docs`).
