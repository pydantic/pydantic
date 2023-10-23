"""Utilities related to attribute docstring extraction."""
from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any, Sequence


class DocstringVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

        self.target: str | None = None
        self.attrs: dict[str, str] = {}
        self.previous_node_type: type[ast.AST] | None = None

    def visit(self, node: ast.AST) -> Any:
        node_result = super().visit(node)
        self.previous_node_type = type(node)
        return node_result

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if isinstance(node.target, ast.Name):
            self.target = node.target.id

    def visit_Expr(self, node: ast.Expr) -> Any:
        if isinstance(node.value, ast.Str) and self.previous_node_type is ast.AnnAssign:
            docstring = inspect.cleandoc(node.value.s)
            if self.target:
                self.attrs[self.target] = docstring
            self.target = None


def extract_docstrings_from_cls(cls: type[Any]) -> dict[str, str]:
    """Map model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.

    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    try:
        lines, _ = inspect.findsource(cls)
    except OSError:
        # Source can't be parsed (maybe because running in an interactive terminal),
        # we don't want to error here.
        return {}
    else:
        source: Sequence[str] = []
        frame = inspect.currentframe()

        # Avoid circular import
        from ._model_construction import ModelMetaclass

        if frame is None:
            return {}

        while frame and frame.f_back:
            if frame.f_code is ModelMetaclass.__new__.__code__:
                lnum = frame.f_back.f_lineno
                if not isinstance(lnum, int):
                    return {}
                source = inspect.getblock(lines[lnum - 1 :])
                break
            frame = frame.f_back

        if not source:
            return {}

    # Required for nested class definitions, e.g. in a function block
    dedent_source = textwrap.dedent(''.join(source))

    visitor = DocstringVisitor()
    visitor.visit(ast.parse(dedent_source))
    return visitor.attrs
