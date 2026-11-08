# Gemma4Paper Part 2 auxiliary arm (pre-registration section 4-1): runs the competition harness inside a benchmark task with a proxied Gemma 4 31B.
# Shard __SHARD__. Tasks are a contiguous slice of the pre-registered permutation (part2_order.tsv). A and B run as a pair per task.
# Competition data is fetched via the Kaggle API into the task runtime's /tmp only (it never leaves Kaggle). Only Gemma models are used.
# Traces and results go to /kaggle/working/out (private task output), the same status as the main-arm kernel output.
import glob, json, os, subprocess, sys, time
from pathlib import Path
import kaggle_benchmarks as kbench

COMP = "gemma-4-developer-agent"
SHARD = "__SHARD__"
TASK_IDS = json.loads('__IDS__')  # placeholder kept inside a string (a bare name would be blocked by the push gate with NameError)
BUNDLES = ["A_baseline", "B_guard"]
T0 = time.time()


def log(*a):
    print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)


@kbench.task(name="gemma4paper aux __SHARD__")
def gemma4paper_aux(llm) -> bool:
    out = {"shard": SHARD, "proxy_model_req": getattr(llm, "model", None) or getattr(llm, "name", None)}
    # Competition data is sent only to Gemma. The generation run uses the default model (Gemini), so stop here.
    if "gemma" not in str(out["proxy_model_req"]).lower():
        print("AUX", json.dumps({"skipped_non_gemma": out["proxy_model_req"]}))
        return False
    # 1. The harness runs in its own venv (mixing it into the benchmark venv raises a protobuf VersionError)
    wh = glob.glob("/kaggle/input/**/gemma-4-developer-agent-wheelhouse", recursive=True)
    skip = ("cutlass", "vllm", "torch", "triton", "nvidia", "flashinfer", "xformers")
    whls = [w for w in glob.glob(wh[0] + "/*.whl") if not any(x in w.lower() for x in skip)]
    H = "/tmp/hv"
    subprocess.run([sys.executable, "-m", "venv", H], check=True)
    pins = []
    for w in whls:
        p = os.path.basename(w).split("-")
        pins.append(f"{p[0].replace('_', '-')}=={p[1]}")
    Path("/tmp/pins.txt").write_text("\n".join(pins))
    r = subprocess.run([H + "/bin/pip", "install", "-q", "--no-deps", *whls], capture_output=True, text=True)
    out["pip_wheelhouse_rc"] = r.returncode
    chk = subprocess.run([H + "/bin/pip", "check"], capture_output=True, text=True).stdout
    miss = sorted({l.split(" requires ")[1].split(",")[0].split()[0] for l in chk.splitlines()
                   if " requires " in l and "which is not installed" in l})
    if miss:
        r = subprocess.run([H + "/bin/pip", "install", "-q", "-c", "/tmp/pins.txt", *miss], capture_output=True, text=True)
        out["pip_deps_rc"] = r.returncode
    log("installed", out)
    # 2. Competition data: /tmp only (/kaggle/working is saved as task output)
    if "KAGGLE_API_TOKEN" not in os.environ and "KAGGLE_API_V1_TOKEN" in os.environ:
        os.environ["KAGGLE_API_TOKEN"] = os.environ["KAGGLE_API_V1_TOKEN"]
    D = Path("/tmp/compdata")
    try:
        subprocess.run([sys.executable, "-m", "venv", "/tmp/kv"], check=True)
        subprocess.run(["/tmp/kv/bin/pip", "install", "-q", "kaggle"], check=True)
        K = "/tmp/kv/bin/kaggle"

        def get(n):
            dst = D / Path(n).parent
            dst.mkdir(parents=True, exist_ok=True)
            r = subprocess.run([K, "competitions", "download", COMP, "-f", n, "-p", str(dst), "-q"], capture_output=True, text=True)
            return None if r.returncode == 0 else (n, (r.stderr or r.stdout)[-160:])

        names, tok = [], ""
        for _ in range(10):
            ls = subprocess.run([K, "competitions", "files", COMP, "--page-size", "200", "-v"] + (["--page-token", tok] if tok else []),
                                capture_output=True, text=True)
            ln = ls.stdout.splitlines()
            names += [l.split(",")[0] for l in ln[1:] if l.strip() and "Next Page Token" not in l]
            tok = next((l.split("= ", 1)[1].strip() for l in ln if "Next Page Token" in l), "")
            if not tok:
                break
        bad = [get("tasks.jsonl")]
        rows = {json.loads(l)["instance_id"]: json.loads(l) for l in open(D / "tasks.jsonl")}
        want = [n for n in names if n.startswith(("wheels/", "sandbox/", "docker/"))]
        for t in TASK_IDS:
            pre = t.split("_")[0]
            c = rows[t]["base_commit"]
            want += [f"snapshots/{t}.tgz", f"graphs/{pre}_{c}.json", f"embeddings/{pre}_{c}.npz"]
        bad += [get(n) for n in dict.fromkeys(want)]
        for z in D.rglob("*.zip"):
            subprocess.run(["unzip", "-o", "-q", str(z), "-d", str(z.parent)]); z.unlink()
        out["files_listed"] = len(names)
        out["data_files"] = sum(1 for _ in D.rglob("*") if _.is_file())
        out["download_fail"] = [b for b in bad if b][:5]
    except Exception as e:
        out["data_err"] = repr(e)[:500]
        print("AUX", json.dumps(out)); return False
    log("data", out["data_files"], out["download_fail"])
    # 3. Evaluation with the harness venv's Python. Results go to a file (the harness captures stdout)
    broot = Path(glob.glob(f"/kaggle/input/**/{BUNDLES[0]}/agent.yaml", recursive=True)[0]).parent.parent
    Path("/tmp/inner.py").write_text(INNER)
    env = dict(os.environ, AUX_MODEL=out["proxy_model_req"], AUX_BROOT=str(broot), AUX_DATA=str(D),
               AUX_TASKS=json.dumps(TASK_IDS), AUX_BUNDLES=json.dumps(BUNDLES), OTEL_SDK_DISABLED="true")
    r = subprocess.run([H + "/bin/python", "/tmp/inner.py"], capture_output=True, text=True, env=env)
    out["inner_rc"] = r.returncode
    if r.returncode:
        out["inner_err"] = r.stderr[-1500:]
    res = Path("/kaggle/working/out/results.jsonl")
    rows = [json.loads(l) for l in open(res)] if res.exists() else []
    out["n_rows"] = len(rows)
    out["n_resolved"] = sum(1 for x in rows if x.get("resolved"))
    out["n_error"] = sum(1 for x in rows if "error" in x)
    out["total_sec"] = round(time.time() - T0, 1)
    for x in rows:
        print("AUXROW", json.dumps(x))
    print("AUX", json.dumps(out, ensure_ascii=False))
    return out["n_rows"] == 2 * len(TASK_IDS)


INNER = r"""
import asyncio, json, os, shutil, time, traceback
from pathlib import Path
import litellm, yaml
from google.adk.models.lite_llm import LiteLlm
from adk_submission import ModelRegistry
from adk_submission.resolvers.generation import install_litellm_reasoning_patch
from swegemma.models.discovery import validate_single_declared_model
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps._configs import EventsCompactionConfig
from swegemma.config import EvalConfig, build_submission_limits
from swegemma.evaluate import Evaluator
from swegemma.models import load_tasks
litellm.drop_params = True
install_litellm_reasoning_patch()
base = os.environ["MODEL_PROXY_URL"].rstrip("/")
for s in ("/openapi", "/genai"):
    if base.endswith(s):
        base = base[: -len(s)]
D = Path(os.environ["AUX_DATA"]); BROOT = Path(os.environ["AUX_BROOT"])
TASK_IDS = json.loads(os.environ["AUX_TASKS"]); BUNDLES = json.loads(os.environ["AUX_BUNDLES"])
OUT = Path("/kaggle/working/out"); OUT.mkdir(parents=True, exist_ok=True)
limits, gen = build_submission_limits()
alltasks = {t.instance_id: t for t in load_tasks(D / "tasks.jsonl")}
evs = {}
for b in BUNDLES:
    agent_dir = Path("/tmp/bundles") / b
    shutil.copytree(BROOT / b, agent_dir, dirs_exist_ok=True)
    declared = validate_single_declared_model(agent_dir)
    models = ModelRegistry()
    for alias in {declared, "gemma-4-31b-it-qat-w4a16-ct"}:
        models.register(alias, LiteLlm(model="openai/" + os.environ["AUX_MODEL"], api_base=base + "/openapi",
                                       api_key=os.environ["MODEL_PROXY_API_KEY"]))
    ec = {}
    if (agent_dir / "eval_config.yaml").exists():
        raw = yaml.safe_load((agent_dir / "eval_config.yaml").read_text())
        ec = raw.get("evaluation", raw) or {}
    res_dir = OUT / b; res_dir.mkdir(parents=True, exist_ok=True)
    cfg = EvalConfig(tasks_path=D / "tasks.jsonl", snapshots_dir=D / "snapshots", results_dir=res_dir,
                     submission_dir=agent_dir, models=models, sandbox="subprocess",
                     timeout_seconds=int(ec.get("timeout_seconds", 300)), max_time_minutes=float(ec.get("max_time_minutes", 60.0)),
                     max_tool_calls=int(ec.get("max_tool_calls", 100)), max_turns=ec.get("max_turns"),
                     limits=limits, generation_constraints=gen, adapter_manifest=None,
                     context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
                     events_compaction_config=EventsCompactionConfig(compaction_interval=15, overlap_size=2,
                                                                     token_threshold=14336, event_retention_size=5),
                     graph_dir=str(D / "graphs"), embeddings_dir=str(D / "embeddings"), wheels_dir=D / "wheels", verbose=False)
    evs[b] = Evaluator(cfg)
for i, tid in enumerate(TASK_IDS, 1):
    for b in BUNDLES:
        t1 = time.time()
        try:
            r = asyncio.run(evs[b].evaluate_task(task=alltasks[tid], task_index=i, total_tasks=len(TASK_IDS)))
            row = {"bundle": b, "id": tid, "resolved": r.resolved, "exit": r.test_exit_code,
                   "patch_chars": len(r.agent_patch or ""), "tool_calls": r.tool_calls,
                   "sec": round(r.duration_seconds, 1), "wall": round(time.time() - t1, 1),
                   # cause of exit -1 / empty patch; shard s1 lacked this field, so 7 of its 18 rows could not be attributed
                   "error": (str(r.error)[-400:] if getattr(r, "error", None) else None)}
        except Exception as e:
            row = {"bundle": b, "id": tid, "error": traceback.format_exc()[-600:], "wall": round(time.time() - t1, 1)}
        with open(OUT / "results.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
"""


gemma4paper_aux.run(kbench.llm)
