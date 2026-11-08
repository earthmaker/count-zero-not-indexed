# Gemma4Paper: feasibility probe running the competition harness on one task inside a benchmark task with a proxied Gemma 31B.
# Competition data is fetched via the Kaggle API inside the task runtime (it never leaves Kaggle). Only Gemma models are used.
# Output is summary numbers only; no code, patch or message text is printed.
import asyncio, concurrent.futures, glob, importlib, json, os, subprocess, sys, time
from pathlib import Path
import kaggle_benchmarks as kbench

COMP = "gemma-4-developer-agent"
TASK = "requests_7315"
COMMIT = "6360477c52303c9445b45fa8744b02d05a2f0905"
BUNDLE = "A_baseline"
T0 = time.time()


def log(*a):
    print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)


@kbench.task(name="gemma4paper harness probe")
def gemma4paper_harness_probe(llm) -> bool:
    out = {"proxy_model_req": getattr(llm, "model", None) or getattr(llm, "name", None)}
    # Competition data is sent only to Gemma. The generation run uses the default model (Gemini), so stop here.
    if "gemma" not in str(out["proxy_model_req"]).lower():
        print("HPROBE", json.dumps({"skipped_non_gemma": out["proxy_model_req"]}))
        return False
    # 1. The harness runs in its own venv (v2: mixing it into the benchmark venv clashes protobuf gencode 6.33 with runtime 5.29)
    wh = glob.glob("/kaggle/input/**/gemma-4-developer-agent-wheelhouse", recursive=True)
    out["wheelhouse"] = wh[:1]
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
    if r.returncode:
        out["pip_err"] = r.stderr[-600:]
    chk = subprocess.run([H + "/bin/pip", "check"], capture_output=True, text=True).stdout
    miss = sorted({l.split(" requires ")[1].split(",")[0].split()[0] for l in chk.splitlines() if " requires " in l and "which is not installed" in l})
    out["missing_deps"] = len(miss)
    if miss:
        r = subprocess.run([H + "/bin/pip", "install", "-q", "-c", "/tmp/pins.txt", *miss], capture_output=True, text=True)
        out["pip_deps_rc"] = r.returncode
        if r.returncode:
            out["pip_deps_err"] = r.stderr[-600:]
    log("installed", out)
    # 2. Competition data (one task's share): /tmp only (/kaggle/working is saved as task output, measured in v2)
    if "KAGGLE_API_TOKEN" not in os.environ and "KAGGLE_API_V1_TOKEN" in os.environ:
        os.environ["KAGGLE_API_TOKEN"] = os.environ["KAGGLE_API_V1_TOKEN"]
    D = Path("/tmp/compdata")
    try:
        subprocess.run([sys.executable, "-m", "venv", "/tmp/kv"], check=True)
        subprocess.run(["/tmp/kv/bin/pip", "install", "-q", "kaggle"], check=True)
        K = "/tmp/kv/bin/kaggle"
        names, tok = [], ""
        for _ in range(10):
            ls = subprocess.run([K, "competitions", "files", COMP, "--page-size", "200", "-v"] + (["--page-token", tok] if tok else []),
                                capture_output=True, text=True)
            ln = ls.stdout.splitlines()
            names += [l.split(",")[0] for l in ln[1:] if l.strip() and "Next Page Token" not in l]
            tok = next((l.split("= ", 1)[1].strip() for l in ln if "Next Page Token" in l), "")
            if not tok:
                break
        out["files_listed"] = len(names)
        want = ["tasks.jsonl", f"snapshots/{TASK}.tgz", f"graphs/{TASK.split('_')[0]}_{COMMIT}.json",
                f"embeddings/{TASK.split('_')[0]}_{COMMIT}.npz"] + [n for n in names if n.startswith(("wheels/", "sandbox/", "docker/"))]
        bad = []
        for n in want:
            dst = D / Path(n).parent
            dst.mkdir(parents=True, exist_ok=True)
            r = subprocess.run([K, "competitions", "download", COMP, "-f", n, "-p", str(dst), "-q"], capture_output=True, text=True)
            if r.returncode:
                bad.append((n, (r.stderr or r.stdout)[-160:]))
        for z in D.rglob("*.zip"):
            subprocess.run(["unzip", "-o", "-q", str(z), "-d", str(z.parent)]); z.unlink()
        out["data_files"] = sum(1 for _ in D.rglob("*") if _.is_file())
        out["download_fail"] = bad[:5]
        if not (D / "tasks.jsonl").exists():
            raise RuntimeError("tasks.jsonl missing")
    except Exception as e:
        out["data_err"] = repr(e)[:500]
        print("HPROBE", json.dumps(out)); return False
    log("data", out.get("data_files"))
    # 3. One evaluation, with the harness venv's Python
    bc = glob.glob(f"/kaggle/input/**/{BUNDLE}/agent.yaml", recursive=True)
    Path("/tmp/inner.py").write_text(INNER)
    env = dict(os.environ, PROBE_MODEL=out["proxy_model_req"], PROBE_AGENT=str(Path(bc[0]).parent), PROBE_DATA=str(D),
               PROBE_TASK=TASK, OTEL_SDK_DISABLED="true")
    t1 = time.time()
    r = subprocess.run([H + "/bin/python", "/tmp/inner.py"], capture_output=True, text=True, env=env, timeout=5400)
    out["inner_rc"] = r.returncode
    out["inner_sec"] = round(time.time() - t1, 1)
    # v3: rc was 0 but stdout had no INNER line, so results are read from a file
    if Path("/tmp/inner.json").exists():
        out.update(json.loads(Path("/tmp/inner.json").read_text()))
    else:
        out["inner_err"] = r.stderr[-1500:]
        out["inner_stdout_lines"] = len(r.stdout.splitlines())
    out["total_sec"] = round(time.time() - T0, 1)
    print("HPROBE", json.dumps(out, ensure_ascii=False))
    return "result" in out


INNER = r"""
import asyncio, json, os, time
from pathlib import Path
out = {}
try:
    import litellm
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
    agent_dir = Path(os.environ["PROBE_AGENT"]); D = Path(os.environ["PROBE_DATA"])
    models = ModelRegistry()
    declared = validate_single_declared_model(agent_dir)
    for alias in {declared, "gemma-4-31b-it-qat-w4a16-ct"}:
        models.register(alias, LiteLlm(model="openai/" + os.environ["PROBE_MODEL"], api_base=base + "/openapi",
                                       api_key=os.environ["MODEL_PROXY_API_KEY"]))
    limits, gen = build_submission_limits()
    res_dir = Path("/tmp/probe_out"); res_dir.mkdir(parents=True, exist_ok=True)
    cfg = EvalConfig(tasks_path=D / "tasks.jsonl", snapshots_dir=D / "snapshots", results_dir=res_dir,
                     submission_dir=agent_dir, models=models, sandbox="subprocess", timeout_seconds=300,
                     max_time_minutes=60.0, max_tool_calls=100, max_turns=None, limits=limits, generation_constraints=gen,
                     adapter_manifest=None,
                     context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
                     events_compaction_config=EventsCompactionConfig(compaction_interval=15, overlap_size=2,
                                                                     token_threshold=14336, event_retention_size=5),
                     graph_dir=str(D / "graphs"), embeddings_dir=str(D / "embeddings"), wheels_dir=D / "wheels", verbose=False)
    task = [t for t in load_tasks(D / "tasks.jsonl") if t.instance_id == os.environ["PROBE_TASK"]][0]
    t1 = time.time()
    r = asyncio.run(Evaluator(cfg).evaluate_task(task=task, task_index=1, total_tasks=1))
    out["result"] = {"resolved": r.resolved, "exit": r.test_exit_code, "patch_chars": len(r.agent_patch or ""), "tool_calls": r.tool_calls, "sec": round(r.duration_seconds, 1), "wall": round(time.time() - t1, 1)}  # field names match the kernel gemma4paper_part2.py (v4: there is no .patch)
    cnt = {}
    for f in res_dir.rglob("*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for st in d.get("steps", []) if isinstance(d, dict) else []:
            o = st.get("observation")
            for x in (o if isinstance(o, list) else [o] if o else []):
                e = ((x or {}).get("extra") or {}) if isinstance(x, dict) else {}
                k = f"{e.get('author')}:{e.get('tool_name')}"
                cnt[k] = cnt.get(k, 0) + 1
    out["tool_counts"] = cnt
except Exception as e:
    import traceback
    out["eval_err"] = traceback.format_exc()[-1500:]
Path("/tmp/inner.json").write_text(json.dumps(out, ensure_ascii=False))
print("INNER " + json.dumps(out, ensure_ascii=False))
"""


gemma4paper_harness_probe.run(kbench.llm)
