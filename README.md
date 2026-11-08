# When count: 0 Means "Not Indexed": code and pre-registration

Code, agent bundles and the frozen analysis for the Kaggle writeup "When `count: 0` Means "Not Indexed": Measuring Whether Code-Graph Gaps Reach a 4-bit Gemma 4 Agent's Conclusions" (Google - The Gemma 4 Developer Agent Paper Track).

Competition data (repository snapshots, call graphs, embeddings, `tasks.jsonl`, patches) are not redistributed here. Scripts that need them read the competition dataset from paths you set (see "Paths").

## Layout

| Folder | Contents | Paper section |
|---|---|---|
| `probes/probe_empty.py` | Interface probe on a synthetic graph: shows that a missing symbol, a mis-specified argument and a truly empty neighbourhood all return `ok` with zero results. Needs the public harness wheel, no competition data. | §3 |
| `probes/` (other files) | Part 1: reference-edit functions, runtime call edges collected while the tests run, recall of the static graph against them, and the per-task statistics. | §4 |
| `bundles/` | The four agent configurations: A (public baseline used as is), B (A plus the empty-answer guard), C (A plus the graph-first block), D (B plus the graph-first block). | §5.1 |
| `kernel/` | Kaggle notebook that runs the bundles on the public tasks (L4 x4) and keeps the traces; `aux/` holds its helper scripts. | §5.1 |
| `coder/trace_events.py` | Rule-based event judge, version 0.2, frozen before any confirmatory output was read. | §5.2 |
| `coder/frozen/` | Frozen confirmatory analysis for P1-P5 (`confirm_p1p5.py`), its self-test log and `MANIFEST.txt`. | §5.4 |
| `coder/scripts/` | The exact commands of the 81-task analysis, plus the descriptive and exploratory measures. | §5.6 |
| `coder/a_lang_sensitivity.py` | Exploratory broadened absence lexicon. | §5.2b |
| `PREREGISTRATION_en.md` | English translation of the pre-registration. The Korean original is the binding text; its SHA-256 is given at the top of the translation. | §5 |

## Hashes posted before release

On 1 November 2026 we posted these SHA-256 values to the competition forum (topic 754667). The post also states that the final 81-task results had been opened on 24 October, before the hashes were posted.

```
0e47607b2d56642e514f4908966f33fbd6bcc4e7a12be495f123095f21d98150  coder/frozen/MANIFEST.txt
ae726b5fe004281ccbf083878ff33c723a29d321096a7ab2e6f1459dc8d08071  coder/frozen/confirm_p1p5.py
5f5d4f98193b81c39626b69be969d89897bcdea50a1b40b65245d6ee7b3ad4f4  coder/frozen/selftest.log
376bdbb4c9cf8925c080e96afa780fce72e2c720ec35caa88d820d86d29cf5ce  coder/trace_events.py
```

These four files are released byte for byte, which is why `coder/trace_events.py` keeps its original Korean comments. `MANIFEST.txt` also lists three derived data files (`gold_vs_graph.json`, `part2_order.tsv`, `part2_strata.tsv`); they are built from competition data and are not included.

Check with `shasum -a 256 <file>` (macOS) or `sha256sum <file>` (Linux). `python3 coder/frozen/confirm_p1p5.py selftest --coder coder` runs the synthetic controls and numeric checks of `selftest.log` and ends with `SELFTEST PASS analysis 1.1`; the last two lines of the log, which read real run outputs, also need the run folders as arguments.

## Paths

Scripts read their inputs from these environment variables; each defaults to a relative path.

| Variable | Meaning |
|---|---|
| `G4P_DATA` | competition dataset root |
| `G4P_DERIVED` | derived tables written by Part 1 |
| `G4P_RUNS` | Part 2 run outputs (results and traces) |
| `G4P_CODER` | this repository's `coder/` folder |
| `G4P_AUDIT`, `G4P_WORK` | audit samples and scratch space |

Harness: swegemma 0.2.7 from the competition wheelhouse of 30 September 2026 (wheel SHA-256 in the paper, §7).

## Attribution and license

Bundle A is the public baseline by Roman Rozen ([notebook](https://www.kaggle.com/code/romanrozen/gemma-eda-baseline-for-a-start-lb-top-1), version 1), used under the Apache License 2.0; bundles B, C and D modify its prompts. See `NOTICE`.

Code and bundles: Apache License 2.0 (`LICENSE`). Documentation, including `PREREGISTRATION_en.md`: CC BY 4.0.
