"""Tests the import and bundle-validation block of the kernel v7 patch without a GPU (local machine, no competition data needed).

Usage: <venv>/bin/python test_kernel_block.py <patched kernel.py> <bundle root>
  1. Does the old import line (swegemma.models.discovery) work in this version? It must fail on 0.2.11 (reproducing the v7 incident = positive control)
  2. Do the patch's import block (cut from the kernel source and exec'd) and the starter notebook's remaining imports work? (torch and vllm are skipped; not installed locally)
  3. Four bundles: adk_submission.validate_directory, the patch's validate_single_declared_model, discover_adapters
  4. Negative control: does the assertion fire on a bundle declaring two models?
  5. How the bundle sampling.yaml thinking_config is passed to vLLM (enable_thinking)
"""
import importlib, json, shutil, sys, tempfile
from pathlib import Path

import adk_submission
import swegemma
import yaml

kernel, root = Path(sys.argv[1]), Path(sys.argv[2])
BUNDLES = ["A_baseline", "B_guard", "C_graphfirst", "D_guard_graphfirst"]
print(f"== swegemma {swegemma.__version__} · adk_submission {adk_submission.__version__}")

# 1
try:
    importlib.import_module("swegemma.models.discovery")
    print("1 old import swegemma.models.discovery: works")
except ModuleNotFoundError as e:
    print("1 old import swegemma.models.discovery: ModuleNotFoundError -", e)

# 2: cut the patch block from the kernel source and run it (test the real thing, not a copy)
src = kernel.read_text()
a = src.index("from adk_submission.discovery import discover_declared_models")
b = src.index("return next(iter(ms))") + len("return next(iter(ms))")
ns = {}
exec(src[a:b], ns)
v1 = ns["validate_single_declared_model"]
from adk_submission import discover_adapters, validate_directory  # noqa: E402
from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits  # noqa: E402
from swegemma.evaluate import Evaluator  # noqa: E402,F401
from swegemma.models import load_tasks  # noqa: E402,F401
from google.adk.agents.context_cache_config import ContextCacheConfig  # noqa: E402,F401
from google.adk.apps._configs import EventsCompactionConfig  # noqa: E402,F401
limits, gen = build_submission_limits()
print("2 import block + starter notebook imports: work | build_submission_limits ->", type(limits).__name__, type(gen).__name__)
try:
    from adk_submission import VllmConfig, VllmServer  # noqa: F401
    print("  VllmConfig/VllmServer import: works")
except Exception as e:  # vllm is not installed locally
    print("  VllmConfig/VllmServer import: fails (", type(e).__name__, ") - the Kaggle wheelhouse has vllm")

# 3
declared = None
for bn in BUNDLES:
    d = root / bn
    vr = validate_directory(d)
    m = v1(d)
    ad = discover_adapters(str(d), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
    declared = declared or m
    print(f"3 {bn:20s} validate_directory={getattr(vr, 'is_valid', vr)!s:5s} model={m} same={m == declared} adapters={len(ad) if hasattr(ad, '__len__') else ad}")

# 4
tmp = Path(tempfile.mkdtemp()) / "two_models"
shutil.copytree(root / "A_baseline", tmp)
p = tmp / "sub_agents" / "code_analyzer.yaml"
p.write_text(p.read_text().replace("model: gemma-4-31b-it-qat-w4a16-ct", "model: gemma-4-12b-it"))
try:
    v1(tmp)
    print("4 negative control (two models): assertion did not fire FAIL")
except AssertionError as e:
    print("4 negative control (two models): assertion fired OK -", e)
except Exception as e:
    print("4 negative control (two models): other exception", type(e).__name__, e)

# 5
from google.adk.models.lite_llm import LiteLlm  # noqa: E402
from adk_submission.resolvers.generation import apply_thinking_config_to_model  # noqa: E402
cfg = yaml.safe_load((root / "A_baseline" / "configs" / "sampling.yaml").read_text())
m = apply_thinking_config_to_model(LiteLlm(model="openai/gemma-4-31b-it-qat-w4a16-ct"), cfg)
print("5 thinking_config", cfg.get("thinking_config"), "→ extra_body", json.dumps(m._additional_args.get("extra_body")),
      "· _adk_include_thoughts", m.__dict__.get("_adk_include_thoughts"))
