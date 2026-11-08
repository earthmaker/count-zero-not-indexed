# Supplement

Values that the paper cites but does not print. Nothing here is a new analysis: each item repeats a result computed for the paper, with its definition. Section numbers refer to the paper.

## S1. Per-repository runtime recall, compared with Chinta (§4.2)

Library-to-library calls only (calls from example applications into the library are excluded on both sides).

| Repository | Chinta's traces [K5] | This work (125 traced tasks) |
|---|---:|---:|
| rich | 15.3% | 14.0% |
| requests | 36.5% | 33.4% |
| fastapi | 39.5% | 50.7% |

Chinta traced each suite once at the repository's latest base commit; we traced each task at its own `base_commit`. The fastapi difference may reflect that sampling difference. In our reading, Chinta's headline 14–21% also counts calls from example applications into the library.

Further Part 1 values:

- With the reference patch applied, 57.0% of tasks with a traced call into the reference-edit function have none of those calls in the graph (the paper reports 61.1% at base).
- Traced functions that could not be aligned to a graph node (relaxed task set): 1,928 of 20,664: lambdas and comprehensions 952, nested functions 673, async functions 303, and no synchronous top-level function or method.
- A relaxed judgeability rule (no test newly broken by the reference patch, at least one test failing at base) gives 121 tasks instead of the strict 109; results go the same way.

## S2. Changes to the plan (§5.1)

The pre-registration's change log (`PREREGISTRATION_en.md`) records each change with its date and reason. The seven changes, and whether any confirmatory output had been seen:

| Date (2026) | Change | Confirmatory output seen? |
|---|---|---|
| 10-06 | Conditions C and D added; P1 measured in C, P3 and P4 as D vs. C, A vs. B auxiliary | No (pilot only) |
| 10-07 | Auxiliary arm through a model proxy stopped after 36 runs (0 resolved; the proxy returned empty responses and the harness discarded the patch) | No |
| 10-07 | Event judge v0.2 frozen, about 30 minutes after the first confirmatory job was launched | No (before any output was read) |
| 10-10 | Harness kept at its 09-30 version after a host update | Yes, 16 tasks |
| 10-10, 10-11 | "Not decidable for lack of opportunity" verdict, for P1 (10-10) and P2 (10-11) | Yes, 32 tasks, descriptive counts |
| 10-11 | Broadened absence lexicon, reported as exploratory (the frozen lexicon missed absence statements in runs with thinking recorded) | Yes |
| 10-12 | Confirmatory analysis script and input hashes fixed, settling nine points the plan left open | Yes, 39 tasks, descriptive counts only (no strata, no tests) |

A separate deviation, in the order of disclosure rather than in the plan: the final 81-task results were opened on 24 October, and the file hashes were posted to the forum on 1 November. The hashes show that these bytes existed on 1 November; the 12 October freeze rests on our own records.

## S3. Causes of empty answers (§5, "Causes of empty answers")

378 empty answers in the confirmatory runs (event level, Wilson 95% intervals). v1 is the rule set fixed before classification; v2 is the revision after a hand audit, used in the paper. v2 adds the category "correct empty answer" (the queried name occurs nowhere in the repository's Python source).

| Cause | v1 | v2 (paper) | v2, audit-corrected |
|---|---:|---:|---:|
| Interface failure (query form) | 258 (68%, 63–73) | 247 (65%, 60–70) | 247 (65%, 60–70) |
| Missing graph content | 30 (8%, 6–11) | 36 (9.5%, 7.0–12.9) | 32 (8.5%, 6.1–11.7) |
| Node without neighbours | 0 (0–1) | 0 (0–1) | 0 (0–1) |
| Correct empty answer | not a category | 53 (14%, 11–18) | 53 (14%, 11–18) |
| Unattributable | 90 (24%, 20–28) | 42 (11%, 8–15) | 46 (12%, 9–16) |

- Audit correction: in v1, case-insensitive matching misclassified 5 of 7 targeted audit cases. In v2, four events where a short name collided with an unrelated module-level name (`Parameters.empty` and `param.empty`, three events, and `response_model`, one) were moved from missing content to unattributable; conclusions are unchanged. Moving three further undecided cases as well would leave 28 under missing content.
- Examples: missing content is mostly async functions and module-level names; unattributable is mostly external or undefined names.
- Task level (76 tasks with any empty answer, v2): interface 68/76, missing content 16/76, correct empty answer 22/76, unattributable 21/76, no neighbours 0.

## S4. Queries for the reference-edit function: two definitions (§5, "Absence conclusions")

Tasks in which the agent queried the graph for the function the reference patch edits, out of 81 per condition.

| Definition | Condition | Tasks querying it | With an empty answer for it | With results for it |
|---|---|---:|---:|---:|
| Pipeline rule (short-name match, dunder names excluded), used in the paper's text | C | 30 | 29 (27 query form, 2 graph gap) | 2 |
| | D | 31 | 26 (24 query form, 2 graph gap) | 11 |
| Frozen P1 rule (last identifier; dunder methods map to their class, `<locals>` to the enclosing function) | C | 31 | 25 with only empty answers | see note |
| | D | 34 | 21 with only empty answers | see note |

Under the pipeline rule, a task can count under both "empty answer" and "results". Under the frozen rule, the remaining tasks (C 6, D 13) are those where not every answer was empty; they may include error responses and are not all "results received".

By stratum (pipeline rule, empty answer for the reference-edit function): C exposed 18/47, covered 9/34; D exposed 16/47, covered 8/34.
