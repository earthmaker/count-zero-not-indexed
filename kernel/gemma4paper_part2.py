"""Gemma4Paper Part 2: runs the bundles (A baseline / B empty-result guard, plus C and D) on public tasks and keeps the traces. Kaggle L4x4 only.

Carries over the install, vLLM and Evaluator setup of the official starter notebook (ryanholbrook/getting-started-gemma-4-developer-agent, 2026-10-01 version)
unchanged; only the task loop, time limit and output collection differ. Output: /kaggle/working/out/<bundle>/{results.jsonl, traces/, logs/}.
The constants (BUNDLES, TASK_IDS, WALL_HOURS) define each run; the first run was a smoke test (A x 3 tasks) to time a task.
"""
import asyncio
import concurrent.futures
import glob
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

T0 = time.time()
BUNDLES = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
# Run v7 = confirmatory run 2: permutation part2_order.tsv
# (seed 20261005) positions 17-52, 36 tasks x A, B, C, D. Not all fit: the run stops at WALL_HOURS (WALL_STOP) and the next run resumes.
# Measured in v6: median 15.5 min real time per task (4 conditions); 4.04 h for 16 tasks; quota counts L4x4 as real time x 4.
# (v6 = positions 1-16, confirmatory run 1 | v5 = C/D smoke test | v4 = A/B pilot; v5 and v4 are outside the confirmatory set)
# Run v9 = confirmatory run 3: from position 33 (fastapi_14303), where v8 hit WALL_STOP, to position 52 (20 tasks; 7 done).
# Run v10 = confirmatory run 4: from position 40 (rich_3905), where v9 hit WALL_STOP,
# to position 81, all 42 remaining tasks. Not all fit: run 5 resumes from the task where it stops.
# Run v11 = confirmatory run 5: from position 61 (rich_3506), where v10 hit WALL_STOP, to position 81, all 21 remaining tasks.
TASK_IDS = ["rich_3506", "fastapi_11194", "rich_3934", "fastapi_14487", "requests_7328", "requests_7505", "rich_3061", "rich_4075", "rich_3772", "fastapi_14873", "fastapi_14301", "fastapi_14262", "fastapi_12942", "rich_3676", "rich_3894", "fastapi_14266", "fastapi_14361", "requests_7502", "fastapi_14962", "rich_3882", "fastapi_14794"]   # empty = all 129 tasks
# WALL_HOURS = (GPU quota hours allotted to this run) / 4 - 0.3 (install and vLLM start-up).
# Pushing without setting it makes the assertion below stop the kernel before any GPU use (almost no quota spent).
WALL_HOURS = 7.0   # v11: v10 measured 6.6 h wall clock for 21 tasks, so all 21 remaining tasks fit
assert WALL_HOURS is not None and 0 < WALL_HOURS <= 8.0, "WALL_HOURS not set: set the quota allotment first (session limit 9h)"
PER_TASK_GUARD_MIN = 65   # maximum one task may take (harness default 60 min + verification)
# Harness version pin check (10-10): the wheelhouse dataset cannot pin a version (metadata dataset_sources always takes the latest) -
# the 10-09 update (swegemma 0.2.7->0.2.11, adk_submission 0.2.12->0.2.13) killed v7 at import. Versions are compared right after install and
# the kernel stops before starting vLLM if they differ from the expected ones.
HARNESS_EXPECT = {"swegemma": "0.2.7", "adk_submission": "0.2.12",
                  # added 10-20: values from the v8/v9 logs (wheelhouse version 30, 10-09). Version 31 (10-12) has the same version strings for these four, identical adk_eval_core and google_adk;
                  # vllm differs by one line in the gemma4.py weight-loading skip list (vision_embedder.). If a version string changes, stop before vLLM.
                  "adk_eval_core": "0.1.0", "google_adk": "1.36.1", "litellm": "1.82.4", "vllm": "0.19.1"}   # pinned to the old versions of pre-registration section 0, same conditions as v6
# Only when pinning old versions: wheels in this folder of the bundle dataset overwrite the wheelhouse install with --no-deps. Otherwise None.
PIN_WHEELS_SUBDIR = "_pinned_harness"   # swegemma-0.2.7 and adk_submission-0.2.12 wheels in the gemma4paper-bundles dataset (10-10 version; sha256 matches the local copies)

# -- 0. GPU gate: die before spending quota unless there are 4 L4 GPUs (push resets the accelerator to the default)
out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip().splitlines()
print("GPU:", out, flush=True)
if len(out) < 4 or not all("L4" in l for l in out):
    print("### GATE: not L4x4 - check that metadata machine_shape=NvidiaL4 and that the push used kaggle CLI 2.x", flush=True)
    sys.exit(0)
# The wheelhouse is cp312 only; the latest image (3.13) fails at install. Use Copy & Edit of the starter notebook to inherit the pinned environment
print("PY:", sys.version.split()[0], flush=True)
if sys.version_info[:2] != (3, 12):
    print("### GATE: not Python 3.12 - Copy & Edit the starter notebook to inherit the pinned environment", flush=True)
    sys.exit(0)

# -- 1. Install (starter notebook cell 1 unchanged)
for k, v in {"LITELLM_LOCAL_MODEL_COST_MAP": "True", "TRANSFORMERS_NO_TF": "1",
             "VLLM_WORKER_MULTIPROC_METHOD": "spawn", "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
             "VLLM_ENGINE_READY_TIMEOUT_S": "1200", "VLLM_NO_USAGE_STATS": "1",
             "OTEL_SDK_DISABLED": "true", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}.items():
    os.environ[k] = v
WHEELHOUSE_DIR = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
if not WHEELHOUSE_DIR.exists():
    cands = glob.glob("/kaggle/input/**/gemma-4-developer-agent-wheelhouse", recursive=True)
    assert cands, f"wheelhouse missing: {os.listdir('/kaggle/input')}"
    WHEELHOUSE_DIR = Path(cands[0])
for pat in ("/usr/local/lib/python*/dist-packages/*cutlass*.pth", "/usr/local/lib/python*/site-packages/*cutlass*.pth"):
    for p in glob.glob(pat):
        try:
            os.unlink(p)
        except OSError:
            pass
tmp_whl = Path("/tmp/wheelhouse")
tmp_whl.mkdir(parents=True, exist_ok=True)
for w in WHEELHOUSE_DIR.glob("*.whl"):
    if "cutlass" in w.name.lower():
        continue
    tn = w.name.replace("cu128", "+cu128") if ("cu128" in w.name and "+" not in w.name) else w.name
    if not (tmp_whl / tn).exists():
        os.symlink(w, tmp_whl / tn)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--force-reinstall",
                *sorted(str(w) for w in tmp_whl.glob("*.whl"))], check=True)
if PIN_WHEELS_SUBDIR:
    pins = sorted(glob.glob(f"/kaggle/input/**/{PIN_WHEELS_SUBDIR}/*.whl", recursive=True))
    assert pins, f"pinned wheels missing: {PIN_WHEELS_SUBDIR}"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--force-reinstall", *pins], check=True)
importlib.invalidate_caches()
import hashlib  # noqa: E402
import importlib.metadata as _im  # noqa: E402

def _ver(d):
    try:
        return _im.version(d)
    except _im.PackageNotFoundError:
        return None


HARNESS = {d: _ver(d) for d in ("swegemma", "adk_submission", "adk_eval_core", "google_adk", "litellm", "vllm")}
for w in sorted(WHEELHOUSE_DIR.glob("*.whl")):
    if w.name.startswith(("swegemma-", "adk_submission-", "adk_eval_core-", "google_adk-", "vllm-", "transformers-", "litellm-", "google_genai-")):
        print("### WHL", w.name, hashlib.sha256(w.read_bytes()).hexdigest(), flush=True)
print("### HARNESS", json.dumps(HARNESS), flush=True)
bad = {k: (HARNESS.get(k), v) for k, v in HARNESS_EXPECT.items() if HARNESS.get(k) != v}
if bad:
    print(f"### GATE: harness versions differ from expected {bad} - adjust HARNESS_EXPECT", flush=True)
    sys.exit(0)
print(f"### INSTALLED {time.time()-T0:.0f}s", flush=True)

# -- 2. Data and bundle locations (mount paths differ between kernels: search, and if missing print the listing and die)
from swegemma.models import load_tasks  # noqa: E402

DATA_DIR = next((Path(c) for c in ("/kaggle/input/competitions/gemma-4-developer-agent",
                                    "/kaggle/input/gemma-4-developer-agent") if Path(c, "tasks.jsonl").exists()), None)
assert DATA_DIR, f"competition data missing: {os.listdir('/kaggle/input')}"
bcands = glob.glob("/kaggle/input/**/A_baseline/agent.yaml", recursive=True)
assert bcands, f"bundle dataset missing: {os.listdir('/kaggle/input')}"
BUNDLE_ROOT = Path(bcands[0]).parent.parent
WORK = Path("/kaggle/working")
OUT = WORK / "out"
OUT.mkdir(parents=True, exist_ok=True)
tasks = load_tasks(DATA_DIR / "tasks.jsonl")
if TASK_IDS:
    tasks = [t for t in tasks if t.instance_id in TASK_IDS]
print(f"### DATA {DATA_DIR} · bundles {BUNDLE_ROOT} · tasks {len(tasks)}", flush=True)
# 10-20: the competition data was re-uploaded on 10-13 (all 524 files have creationDate 10-13; sizes equal the 10-04 copy except README).
# A fingerprint is printed to check identical content afterwards. 10-04 copy: tasks e4b3fd60f69dbc2b, graphs 127 813e9386da326fad.
_acc = hashlib.sha256()
for _g in sorted(glob.glob(str(DATA_DIR / "graphs" / "*.json"))):
    _acc.update((os.path.basename(_g) + "\t" + hashlib.sha256(Path(_g).read_bytes()).hexdigest() + "\n").encode())
print("### DATAFP tasks", hashlib.sha256((DATA_DIR / "tasks.jsonl").read_bytes()).hexdigest()[:16],
      "graphs", len(glob.glob(str(DATA_DIR / "graphs" / "*.json"))), _acc.hexdigest()[:16], flush=True)
_fp = (hashlib.sha256((DATA_DIR / "tasks.jsonl").read_bytes()).hexdigest()[:16], _acc.hexdigest()[:16])
if _fp != ("e4b3fd60f69dbc2b", "813e9386da326fad"):
    print(f"### GATE: competition data fingerprint differs from runs 1-3 (10-04 copy) {_fp} - changed graphs would move the exposure strata. Stopping before vLLM", flush=True)
    sys.exit(0)

# -- 3. vLLM (starter notebook cell 4 unchanged; no bundle has an adapter, so the server starts once)
import litellm  # noqa: E402
import torch  # noqa: E402
from adk_submission import VllmConfig, VllmServer, discover_adapters  # noqa: E402
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS  # noqa: E402
# swegemma 0.2.11 removed swegemma.models.discovery (10-09). The old validate_single_declared_model only called
# this adk_submission function with normalize_model_name and asserted "exactly one", so it is carried over as is.
# It exists in both adk_submission 0.2.12 and 0.2.13, so it runs on either version.
from adk_submission.discovery import discover_declared_models  # noqa: E402


def _norm_model(name: str) -> str:   # verbatim from swegemma 0.2.7 models/discovery.py normalize_model_name
    v = name.strip().lower()
    for p in ("openai/", "google/", "hosted_vllm/", "custom/"):
        if v.startswith(p):
            v = v[len(p):]
    return v


def validate_single_declared_model(agent_dir) -> str:
    ms = discover_declared_models(agent_dir, normalize_fn=_norm_model)
    assert len(ms) == 1, f"declared models are not exactly one: {sorted(ms)} ({agent_dir})"
    return next(iter(ms))

litellm.drop_params = True
TARGET = "gemma-4-31b-it-qat-w4a16-ct"
mp = glob.glob("/kaggle/input/models/google/gemma-4/*/gemma-4-31b-it-qat-w4a16-ct/*/config.json")
assert mp, f"model missing: {glob.glob('/kaggle/input/models/**', recursive=False)}"
MODEL_PATH = Path(mp[0]).parent
first = WORK / "bundles" / BUNDLES[0]
shutil.copytree(BUNDLE_ROOT / BUNDLES[0], first, dirs_exist_ok=True)
declared = validate_single_declared_model(first)
for b in BUNDLES[1:]:   # all four bundles must declare the same single model; the server starts once from the first bundle
    assert validate_single_declared_model(BUNDLE_ROOT / b) == declared, f"{b} declares a model other than {declared}"
adapters = discover_adapters(str(first), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
server = VllmServer(VllmConfig(
    model=str(MODEL_PATH), port=8000, host="127.0.0.1", tool_call_parser="gemma4", reasoning_parser="gemma4",
    max_model_len=32768, dtype="bfloat16" if torch.cuda.is_bf16_supported() else "auto",
    gpu_memory_utilization=0.90, enable_auto_tool_choice=True, enable_lora=True, max_loras=8, max_lora_rank=128,
    tensor_parallel_size=4, startup_timeout=60 * 20), adapter_manifest=adapters)
server.start()
models = server.create_model_registry(aliases=[declared, TARGET], model_prefix="openai/", api_key="EMPTY")
print(f"### VLLM_READY {time.time()-T0:.0f}s", flush=True)

# -- 4. Task loop (EvalConfig of starter notebook cell 5 unchanged; only the bundle is swapped)
import yaml  # noqa: E402
from google.adk.agents.context_cache_config import ContextCacheConfig  # noqa: E402
from google.adk.apps._configs import EventsCompactionConfig  # noqa: E402
from swegemma.config import EvalConfig, build_submission_limits  # noqa: E402
from swegemma.evaluate import Evaluator  # noqa: E402


def run_sync(fn):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(fn())).result()
    return asyncio.run(fn())


limits, gen_constraints = build_submission_limits()
evs = {}
for b in BUNDLES:
    agent_dir = WORK / "bundles" / b
    shutil.copytree(BUNDLE_ROOT / b, agent_dir, dirs_exist_ok=True)
    ec = {}
    if (agent_dir / "eval_config.yaml").exists():
        raw = yaml.safe_load((agent_dir / "eval_config.yaml").read_text())
        ec = raw.get("evaluation", raw) or {}
    res_dir = OUT / b
    cfg = EvalConfig(
        tasks_path=DATA_DIR / "tasks.jsonl", snapshots_dir=DATA_DIR / "snapshots", results_dir=res_dir,
        submission_dir=agent_dir, models=models, sandbox="subprocess",
        timeout_seconds=int(ec.get("timeout_seconds", 300)), max_time_minutes=float(ec.get("max_time_minutes", 60.0)),
        max_tool_calls=int(ec.get("max_tool_calls", 100)), max_turns=ec.get("max_turns"),
        limits=limits, generation_constraints=gen_constraints, adapter_manifest=adapters,
        context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
        events_compaction_config=EventsCompactionConfig(compaction_interval=15, overlap_size=2,
                                                        token_threshold=14336, event_retention_size=5),
        graph_dir=str(DATA_DIR / "graphs"), embeddings_dir=str(DATA_DIR / "embeddings"),
        wheels_dir=DATA_DIR / "wheels", verbose=False)
    evs[b] = Evaluator(cfg)
    res_dir.mkdir(parents=True, exist_ok=True)

# Tasks outer, conditions inner (10-07): hitting the time limit never breaks pairs between conditions (in the old version bundles were outer,
# so later bundles were dropped entirely at the limit). Tasks follow TASK_IDS order (the pre-registered permutation).
by_id = {t.instance_id: t for t in tasks}
order = [by_id[x] for x in TASK_IDS if x in by_id] if TASK_IDS else tasks
for i, t in enumerate(order, 1):
    if (time.time() - T0) / 3600 + PER_TASK_GUARD_MIN / 60 > WALL_HOURS:
        print(f"### WALL_STOP before task {i} {t.instance_id}", flush=True)
        break
    for b in BUNDLES:
        t1 = time.time()
        try:
            r = run_sync(lambda: evs[b].evaluate_task(task=t, task_index=i, total_tasks=len(order)))
            row = {"bundle": b, "id": t.instance_id, "resolved": r.resolved, "exit": r.test_exit_code,
                   "patch_chars": len(r.agent_patch or ""), "tool_calls": r.tool_calls,
                   "sec": round(r.duration_seconds, 1), "wall": round(time.time() - t1, 1),
                   "error": (str(r.error)[-400:] if getattr(r, "error", None) else None)}
        except Exception as e:  # if one task dies, move on to the next; the record is kept
            row = {"bundle": b, "id": t.instance_id, "error": repr(e)[-500:], "wall": round(time.time() - t1, 1)}
        with open(OUT / b / "results.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
        print("### TASK", json.dumps(row), flush=True)

server.stop() if hasattr(server, "stop") else None
print(f"### DONE {time.time()-T0:.0f}s", flush=True)
