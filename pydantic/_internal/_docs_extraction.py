"""Utilities related to attribute docstring extraction."""
from __future__ import annotations

import ast
import inspect
import re
import textwrap
from typing import Any


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


def _extract_source_from_frame(cls_name: str) -> list[str] | None:
    frame = inspect.currentframe()

    while frame:
        lnum = frame.f_lineno
        try:
            lines, _ = inspect.findsource(frame)
        except OSError:
            # Source can't be parsed (maybe because running in an interactive terminal),
            # we don't want to error here.
            pass
        if isinstance(lnum, int) and len(lines) >= lnum and re.match(fr'class\s+{cls_name}', lines[lnum - 1].strip()):
            return inspect.getblock(lines[lnum - 1 :])  # type: ignore
        frame = frame.f_back


def extract_docstrings_from_cls(cls: type[Any]) -> dict[str, str]:
    """Map model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.

    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    # We first try to fetch the source lines by walking back the frames:
    source = _extract_source_from_frame(cls.__name__)

    if not source:
        # Fallback to how inspect fetch the source lines, might not work as expected
        # if two classes have the same name in the same source file.
        try:
            source, _ = inspect.getsourcelines(cls)
        except OSError:
            return {}

    # Required for nested class definitions, e.g. in a function block
    dedent_source = textwrap.dedent(''.join(source))
    if not dedent_source.startswith('class'):
        # We are in the case where there's a dedented (usually multiline) string
        # at a lower indentation level than the class itself. We wrap our class
        # in a function as a workaround.
        dedent_source = f'def _():\n{dedent_source}'

    visitor = DocstringVisitor()
    visitor.visit(ast.parse(dedent_source))
    return visitor.attrs
