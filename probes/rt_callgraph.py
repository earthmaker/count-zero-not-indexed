"""pytest plugin collecting runtime call edges. Gemma4Paper Part 1.

During a pytest run, sys.setprofile collects Python function calls (caller -> callee) and keeps only edges between
repository code as JSON. This is the "ground truth" side against which the competition graph (static AST `calls` edges) is scored for recall.

    RT_ROOT=<repository root> RT_OUT=<output.json> python -m pytest -p rt_callgraph <tests>

Node key is (repository-relative path, co_qualname, co_firstlineno). Matching to graph node names is a separate step.
Each callee gets static properties (async, decorator count, generator); each edge gets a call-site property (does the callee name
appear literally on the calling line = would it plausibly be visible statically).
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import threading

_ROOT = os.path.realpath(os.environ.get('RT_ROOT', os.getcwd()))
_OUT = os.environ.get('RT_OUT', os.path.join(_ROOT, 'rt_edges.json'))
_SKIP_PARTS = ('site-packages', 'dist-packages', os.sep + '.venv' + os.sep, os.sep + 'lib' + os.sep + 'python')

_edges: dict[tuple, dict] = {}
_nodes: dict[tuple, dict] = {}
_lock = threading.Lock()
_in_repo_cache: dict[str, str | None] = {}


def _rel(filename: str) -> str | None:
    r = _in_repo_cache.get(filename)
    if r is not None or filename in _in_repo_cache:
        return r
    out = None
    if filename and not filename.startswith('<'):
        real = os.path.realpath(filename)
        if real.startswith(_ROOT + os.sep) and not any(p in real for p in _SKIP_PARTS):
            out = os.path.relpath(real, _ROOT)
    _in_repo_cache[filename] = out
    return out


def _key(code) -> tuple | None:
    rel = _rel(code.co_filename)
    if rel is None:
        return None
    return (rel, getattr(code, 'co_qualname', code.co_name), code.co_firstlineno)


def _node_info(code) -> dict:
    flags = code.co_flags
    info = {
        'is_async': bool(flags & inspect.CO_COROUTINE) or bool(flags & inspect.CO_ASYNC_GENERATOR),
        'is_generator': bool(flags & inspect.CO_GENERATOR),
        'n_decorators': 0,
        'is_lambda_or_comp': code.co_name.startswith('<'),
    }
    try:
        lines, _ = inspect.findsource(code)
        i = code.co_firstlineno - 1
        # decorators are the lines above def (starting with '@', no blank lines)
        j = i
        while j - 1 >= 0 and lines[j - 1].lstrip().startswith('@'):
            j -= 1
        info['n_decorators'] = i - j if lines[i].lstrip().startswith(('def ', 'async def ', 'class ')) else 0
        if lines[i].lstrip().startswith('@'):  # when firstlineno points at a decorator line
            k = i
            while k < len(lines) and lines[k].lstrip().startswith('@'):
                k += 1
            info['n_decorators'] = k - i
    except Exception:
        pass
    return info


def _call_line_has_name(frame, callee_name: str) -> bool | None:
    """Does the callee name appear literally on the call-site line? If not, the call counts as hard for static analysis to see."""
    try:
        line = inspect.getframeinfo(frame, context=1).code_context
        if not line:
            return None
        return callee_name.split('.')[-1] in line[0]
    except Exception:
        return None


def _profile(frame, event, arg):
    if event != 'call':
        return
    callee = frame.f_code
    ck = _key(callee)
    if ck is None:
        return
    caller_frame = frame.f_back
    if caller_frame is None:
        return
    rk = _key(caller_frame.f_code)
    with _lock:
        if ck not in _nodes:
            _nodes[ck] = _node_info(callee)
        if rk is None:
            return  # call coming from outside the repository (library, pytest): used only as an entry point
        ek = (rk, ck)
        e = _edges.get(ek)
        if e is None:
            if rk not in _nodes:
                _nodes[rk] = _node_info(caller_frame.f_code)
            _edges[ek] = {
                'n': 1,
                'line': caller_frame.f_lineno,
                'name_on_line': _call_line_has_name(caller_frame, callee.co_name),
            }
        else:
            e['n'] += 1


def pytest_configure(config):
    sys.setprofile(_profile)
    threading.setprofile(_profile)


def pytest_unconfigure(config):
    sys.setprofile(None)
    threading.setprofile(None)
    nodes = [{'path': k[0], 'qualname': k[1], 'lineno': k[2], **v} for k, v in _nodes.items()]
    edges = [{'caller': list(a), 'callee': list(b), **v} for (a, b), v in _edges.items()]
    with open(_OUT, 'w', encoding='utf-8') as f:
        json.dump({'root': _ROOT, 'nodes': nodes, 'edges': edges}, f)
    sys.stderr.write(f'[rt_callgraph] nodes={len(nodes)} edges={len(edges)} -> {_OUT}\n')
