"""Utilities related to attribute docstring extraction."""
from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any, Iterable


def _get_assign_targets(node: ast.Assign | ast.AnnAssign) -> Iterable[str]:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Tuple):
                yield from (el.id for el in target.elts)
            else:
                yield target.id
    else:
        # `target` can only be `ast.Name` in the context of a `BaseModel` subclass definition
        yield node.target.id


def _extract_docs(cls_def: ast.ClassDef) -> dict[str, str]:

    nodes_docs_pairs = [
        (node, inspect.cleandoc(next_node.value.s))
        for node, next_node in zip(cls_def.body, cls_def.body[1:])
        if isinstance(node, (ast.Assign, ast.AnnAssign))  # e.g. a: int / a = 1...
        if isinstance(next_node, ast.Expr)  # ...with next_node being a docstring
        if isinstance(next_node.value, ast.Str)
    ]

    doc_mapping: dict[str, str] = {}

    for node, docs in nodes_docs_pairs:
        for target in _get_assign_targets(node):
            doc_mapping[target] = docs

    return doc_mapping


def extract_docstrings_from_cls(cls: type[Any]) -> dict[str, str]:
    """Returns a mapping of the model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.
    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    try:
        source = inspect.getsource(cls)
    except OSError:
        # Source can't be parsed (maybe because running in an interactive terminal)
        # TODO should we issue a UserWarning to indicate that docstrings won't be
        # taken into account?
        return {}

    text = textwrap.dedent(source)

    tree = ast.parse(text).body[0]
    if not isinstance(tree, ast.ClassDef):
        raise TypeError(f"Expected '{ast.ClassDef.__name__}', but received '{cls}' instead")
    return _extract_docs(tree)
