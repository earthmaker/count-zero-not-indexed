---
name: empty-result-check
description: Use when a code-graph tool (get_code_neighbors, search_similar_code, get_code_subgraph) returns count 0 or an empty list. Explains that count 0 is unconfirmed and how to verify a symbol with grep before concluding.
---

# Empty-result check for code-graph tools

The graph tools report `{"status": "ok", ..., "count": 0}` for three different situations that look identical:
1. the node is not in the graph (e.g. async functions, or the name is spelled differently from the stored node name),
2. the query was malformed (wrong `edge_type`, natural language or a short name given to `search_similar_code`),
3. the thing really does not exist.

So `count: 0` is **unconfirmed**, never proof of absence.

## Procedure
1. Verify the symbol exists: `run_command` with `grep -rn "<symbol>" --include=*.py . | head -30` (or `rg -n "<symbol>" -t py | head -30`).
2. If grep finds it, use the exact node name from the grep hit (qualified as the graph prints it) and retry the graph tool once. If it still returns 0, stay with grep and `read_file`.
3. If grep also finds nothing, widen it (partial name, `git log -S`) before concluding the symbol is absent.
4. Never pass `edge_type` to `get_code_neighbors`. The documented value `'CALLS'` matches nothing because stored edge types are lower-case; omit the argument.
5. `search_similar_code` is an exact lookup of a node name or code text. Give it one exact node name only, never a sentence, a short name or a code fragment.
