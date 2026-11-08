"""Part 1 (b): for each of the 129 tasks, run the tests on the base snapshot + test_patch and collect runtime call edges.

Uses a harness-equivalent environment without Docker (rt313 = python3.13 + deduplicated wheels). Because the public harness picks
the newest wheels regardless of the task, old snapshots die during collection; so for each task the highest version satisfying
that commit's pyproject dependency ranges is laid over as an overlay. Each task is extracted, measured and deleted (disk is tight).
With MODE=gold the reference patch is applied first and output goes to rt_out_gold/ (does the reference pass in our environment = judgeable-task denominator, auxiliary trace).
Output: rt_out/<id>.json (edges), <id>.meta.json (run summary), <id>.junit.xml
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

H = Path.home() / "gemma4paper"
D = H / "data"
MODE = os.environ.get("MODE", "base")   # base: base+test_patch | gold: base+patch+test_patch (reference check, auxiliary trace)
OUT = H / ("rt_out" if MODE == "base" else "rt_out_gold")
WK = H / ("rt_work" if MODE == "base" else "rt_work_gold")
OUT.mkdir(exist_ok=True)
WK.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location("sbx", D / "sandbox/setup.py")
sbx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbx)
PY313 = str(H / "rt313/bin/python")
UVENV = dict(os.environ, PATH=str(Path.home() / ".local/bin") + ":" + os.environ["PATH"])
tasks = [json.loads(l) for l in open(D / "tasks.jsonl")]
only = set(sys.argv[1:])

WH: dict[str, list] = {}
for f in (D / "wheels").glob("*.whl"):
    n, v = f.name.split("-")[:2]
    if "-cp3" in f.name and "cp313" not in f.name:
        continue
    WH.setdefault(re.sub(r"[-_.]+", "_", n).lower(), []).append((Version(v), f))


def norm(n):
    return re.sub(r"[-_.]+", "_", n).lower()


def pin_overlay(ws: Path, ov: Path) -> dict:
    """If the highest version satisfying the pyproject range differs from the newest wheel, install that version into the overlay."""
    pins = {}
    try:
        deps = tomllib.load(open(ws / "pyproject.toml", "rb")).get("project", {}).get("dependencies", [])
    except Exception:
        deps = []
    for d in deps:
        try:
            r = Requirement(d)
        except Exception:
            continue
        c = WH.get(norm(r.name), [])
        if len(c) < 2:
            continue
        ok = sorted((x for x in c if x[0] in r.specifier), key=lambda x: x[0])
        if ok and ok[-1][0] != max(x[0] for x in c):
            pins[norm(r.name)] = ok[-1][1]
    if pins:
        subprocess.run(["uv", "pip", "install", "-q", "--no-deps", "--target", str(ov)] + [str(p) for p in pins.values()],
                       capture_output=True, env=UVENV)
    return {k: p.name for k, p in pins.items()}


def test_files(tp: str) -> list[str]:
    fs = []
    for l in tp.splitlines():
        if l.startswith("+++ "):
            p = l[4:].strip()
            p = p[2:] if p.startswith("b/") else p
            if p.endswith(".py") and re.search(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$", p):
                fs.append(p)
    return fs


def run(t):
    iid = t["instance_id"]
    meta = OUT / f"{iid}.meta.json"
    if meta.exists():
        return iid, "skip"
    ws = WK / iid
    ov = WK / (iid + "_ov")
    shutil.rmtree(ws, ignore_errors=True)
    shutil.rmtree(ov, ignore_errors=True)
    ws.mkdir()
    m = {"id": iid, "t0": time.time()}
    try:
        with tarfile.open(D / "snapshots" / f"{iid}.tgz") as tf:
            tf.extractall(ws, filter="fully_trusted")
        if MODE == "gold":
            (ws / "_gp.diff").write_text(t["patch"].rstrip("\n") + "\n")
            gp = subprocess.run(["git", "apply", "--whitespace=nowarn", "_gp.diff"], cwd=ws, capture_output=True, text=True)
            m["gold_apply_rc"] = gp.returncode
            m["gold_apply_err"] = gp.stderr[-300:]
            (ws / "_gp.diff").unlink()
        (ws / "_tp.diff").write_text(t["test_patch"].rstrip("\n") + "\n")
        ap = subprocess.run(["git", "apply", "--whitespace=nowarn", "_tp.diff"], cwd=ws, capture_output=True, text=True)
        m["apply_rc"] = ap.returncode
        m["apply_err"] = ap.stderr[-300:]
        (ws / "_tp.diff").unlink()
        m["pins"] = pin_overlay(ws, ov)
        sbx.configure_workspace_pytest_ini(ws)
        sbx.configure_workspace_conftest(ws)
        tfs = [f for f in test_files(t["test_patch"]) if (ws / f).exists()]
        m["tests"] = tfs
        env = dict(os.environ, PYTHONPATH=f"{ws}:{ws / 'src'}:{ov}:{H}", RT_ROOT=str(ws),
                   RT_OUT=str(OUT / f"{iid}.json"), TEST_TMPDIR="/tmp", PYTHONDONTWRITEBYTECODE="1")
        pkg = t["repo"].split("/")[1].lower()
        chk = subprocess.run([PY313, "-c", f"import {pkg};print({pkg}.__file__)"], cwd=ws, env=env,
                             capture_output=True, text=True)
        m["pkg_file"] = (chk.stdout or chk.stderr).strip()[-200:]
        cmd = [PY313, "-m", "pytest", "-p", "rt_callgraph", "-o", "filterwarnings=ignore", "-q",
               "-p", "no:cacheprovider", f"--junitxml={OUT / (iid + '.junit.xml')}"] + tfs
        try:
            r = subprocess.run(cmd, cwd=ws, env=env, capture_output=True, text=True, timeout=1200)
            m["rc"] = r.returncode
            m["tail"] = r.stdout[-600:]
        except subprocess.TimeoutExpired:
            m["rc"] = "timeout"
    except Exception as e:
        m["error"] = repr(e)[-400:]
    finally:
        shutil.rmtree(ws, ignore_errors=True)
        shutil.rmtree(ov, ignore_errors=True)
    m["sec"] = round(time.time() - m["t0"], 1)
    m["has_edges"] = (OUT / f"{iid}.json").exists()
    meta.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    return iid, m.get("rc")


todo = [t for t in tasks if not only or t["instance_id"] in only]
with ThreadPoolExecutor(int(os.environ.get("NJ", "6"))) as ex:
    for i, (iid, rc) in enumerate(ex.map(run, todo), 1):
        print(i, iid, rc, flush=True)
