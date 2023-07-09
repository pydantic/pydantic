from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any


def _extract_docs(lines: list[str], cls_def: ast.ClassDef) -> dict[str, str]:
    return {
        target: comments
        for node, comments in (
            (node, inspect.cleandoc(next_node.value.s))
            for node, next_node in zip(cls_def.body, cls_def.body[1:])
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            if isinstance(next_node, ast.Expr)
            if isinstance(next_node.value, ast.Str)
        )
        for target in ('TODO',)
    }


def extract_docstrings_from_cls(cls: type[Any]) -> dict[str, str]:
    try:
        source = inspect.getsource(cls)
    except OSError:
        # Source can't be parse (maybe because in an interactive terminal)
        # TODO should we issue a UserWarning to indicate that docstrings won't be
        # taken into account?
        return {}

    text = textwrap.dedent(source)
    lines = source.splitlines(keepends=True)

    tree = ast.parse(text).body[0]
    if not isinstance(tree, ast.ClassDef):
        raise TypeError(f"Expected '{ast.ClassDef.__name__}', but received '{cls}' instead")
    return _extract_docs(lines, tree)
