"""Does search_similar_code accept code fragments? Full node source vs. partial source (first 3 lines) vs. source with one whitespace changed. Sample of 30 tasks."""
import os
import json, random
from swegemma.tools import graph as tg
D = os.environ.get("G4P_DATA", "data")  # competition data dir (attached Kaggle dataset)
tasks = [json.loads(l) for l in open(D + "/tasks.jsonl")]
class Ctx:
    max_stdout_chars = 5000; graph_dir = D + "/graphs"; embeddings_dir = D + "/embeddings"
    def __init__(s, t): s.repo = t["repo"]; s.task = {"repo": t["repo"], "base_commit": t["base_commit"], "instance_id": t["instance_id"]}
    def check_budget(s, count_tool_call=True): return None
rnd = random.Random(1); res = {"whole": [], "first3": [], "ws": []}
for t in rnd.sample(tasks, 30):
    g = json.load(open(f"{D}/graphs/{t['repo'].split('/')[1]}_{t['base_commit']}.json"))
    ns = [n for n in g["nodes"] if (n.get("text") or "").count("\n") >= 4]
    n = rnd.choice(ns); c = Ctx(t); txt = n["text"]
    for k, q in (("whole", txt), ("first3", "\n".join(txt.splitlines()[:3])), ("ws", txt.replace("\n", "\n ", 1))):
        r = json.loads(tg.search_similar_code(c, q, 5)); res[k].append((r.get("status"), r.get("count")))
for k, v in res.items():
    print(k, "ok/0", sum(1 for x in v if x == ("ok", 0)), "ok>0", sum(1 for x in v if x[0] == "ok" and x[1]), "/", len(v))
