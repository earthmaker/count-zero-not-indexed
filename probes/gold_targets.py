"""Find the functions edited by the reference patch (unified diff) via the AST of the base snapshot. Gemma4Paper Part 1.

    python gold_targets.py <repository root (base commit)> <patch file>

Reports the innermost function/method enclosing each changed line (deleted lines use the original line number; added lines use the neighbouring original line numbers).
Changes outside functions (module level, class body) are counted separately as `<module>` or the class name: places that may have no graph node.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys

HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def changed_old_lines(patch: str) -> dict[str, set[int]]:
    """Changed line numbers per file, relative to the original (base). Pure additions attach to the preceding original line."""
    out: dict[str, set[int]] = {}
    cur = None
    old = 0
    for line in patch.splitlines():
        if line.startswith('--- '):
            continue
        if line.startswith('+++ '):
            p = line[4:].strip()
            cur = p[2:] if p.startswith(('a/', 'b/')) else p
            if cur == '/dev/null':
                cur = None
            continue
        m = HUNK.match(line)
        if m:
            old = int(m.group(1))
            continue
        if cur is None or not cur.endswith('.py'):
            continue
        if line.startswith('-'):
            out.setdefault(cur, set()).add(old)
            old += 1
        elif line.startswith('+'):
            out.setdefault(cur, set()).add(max(old - 1, 1))
        elif line.startswith(' '):
            old += 1
    return out


class _Scopes(ast.NodeVisitor):
    def __init__(self):
        self.scopes = []  # (start, end, qualname, kind, is_async, n_decorators)
        self.stack = []

    def _push(self, node, kind):
        name = '.'.join(self.stack + [node.name])
        start = min([d.lineno for d in getattr(node, 'decorator_list', [])] + [node.lineno])
        self.scopes.append((start, node.end_lineno, name, kind,
                            isinstance(node, ast.AsyncFunctionDef), len(getattr(node, 'decorator_list', []))))
        self.stack.append(node.name if kind == 'class' else node.name + '.<locals>')
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self._push(node, 'function')

    def visit_AsyncFunctionDef(self, node):
        self._push(node, 'function')

    def visit_ClassDef(self, node):
        self._push(node, 'class')


def targets(root: str, patch: str) -> list[dict]:
    res = {}
    for path, lines in changed_old_lines(patch).items():
        full = os.path.join(root, path)
        if not os.path.exists(full):
            res[(path, '<new file>')] = {'path': path, 'qualname': '<new file>', 'kind': 'new_file'}
            continue
        tree = ast.parse(open(full, encoding='utf-8').read())
        v = _Scopes()
        v.visit(tree)
        for ln in lines:
            inner = [s for s in v.scopes if s[0] <= ln <= s[1]]
            if not inner:
                key = (path, '<module>')
                res.setdefault(key, {'path': path, 'qualname': '<module>', 'kind': 'module'})
                continue
            s = max(inner, key=lambda s: s[0])  # innermost
            qual = s[2].replace('.<locals>.', '.<locals>.')
            key = (path, qual)
            res.setdefault(key, {'path': path, 'qualname': qual, 'kind': s[3], 'is_async': s[4],
                                 'n_decorators': s[5], 'start': s[0], 'end': s[1]})
    return list(res.values())


if __name__ == '__main__':
    print(json.dumps(targets(sys.argv[1], open(sys.argv[2], encoding='utf-8').read()), indent=1, ensure_ascii=False))
