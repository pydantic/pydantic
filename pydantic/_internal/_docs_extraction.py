"""Utilities related to attribute docstring extraction."""

from __future__ import annotations

import ast
import inspect
import sys
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
        if (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and self.previous_node_type is ast.AnnAssign
        ):
            docstring = inspect.cleandoc(node.value.value)
            if self.target:
                self.attrs[self.target] = docstring
            self.target = None


def _dedent_source_lines(source: list[str]) -> str:
    # Required for nested class definitions, e.g. in a function block
    dedent_source = textwrap.dedent(''.join(source))
    if dedent_source.startswith((' ', '\t')):
        # We are in the case where there's a dedented (usually multiline) string
        # at a lower indentation level than the class itself. We wrap our class
        # in a function as a workaround.
        dedent_source = f'def dedent_workaround():\n{dedent_source}'
    return dedent_source


def _extract_source_from_frame(cls: type[Any]) -> list[str] | None:
    frame = inspect.currentframe()

    while frame:
        if inspect.getmodule(frame) is inspect.getmodule(cls):
            lnum = frame.f_lineno
            try:
                lines, _ = inspect.findsource(frame)
            except OSError:  # pragma: no cover
                # Source can't be retrieved (maybe because running in an interactive terminal),
                # we don't want to error here.
                pass
            else:
                block_lines = inspect.getblock(lines[lnum - 1 :])
                dedent_source = _dedent_source_lines(block_lines)
                try:
                    block_tree = ast.parse(dedent_source)
                except SyntaxError:
                    pass
                else:
                    stmt = block_tree.body[0]
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == 'dedent_workaround':
                        # `_dedent_source_lines` wrapped the class around the workaround function
                        stmt = stmt.body[0]
                    if isinstance(stmt, ast.ClassDef) and stmt.name == cls.__name__:
                        return block_lines

        frame = frame.f_back


def extract_docstrings_from_cls(cls: type[Any], use_inspect: bool = False) -> dict[str, str]:
    """Map model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.
        use_inspect: Whether to skip usage of frames to find the object and use
            the `inspect` module instead.

    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    # For TypedDict, we need to collect docstrings from the entire MRO
    # to handle inheritance properly, since TypedDict fields are re-derived
    # from merged annotations rather than reusing parent FieldInfo instances.
    from typing_extensions import is_typeddict

    if is_typeddict(cls):
        return _extract_docstrings_from_mro(cls, use_inspect)
    
    if use_inspect or sys.version_info >= (3, 13):
        # On Python < 3.13, `inspect.getsourcelines()` might not work as expected
        # if two classes have the same name in the same source file.
        # On Python 3.13+, it will use the new `__firstlineno__` class attribute,
        # making it way more robust.
        try:
            source, _ = inspect.getsourcelines(cls)
        except OSError:  # pragma: no cover
            return {}
    else:
        # TODO remove this implementation when we drop support for Python 3.12:
        source = _extract_source_from_frame(cls)

    if not source:
        return {}

    dedent_source = _dedent_source_lines(source)

    visitor = DocstringVisitor()
    visitor.visit(ast.parse(dedent_source))
    return visitor.attrs


def _extract_docstrings_from_mro(cls: type[Any], use_inspect: bool) -> dict[str, str]:
    """Extract docstrings from a class and its bases in MRO order.
    
    For TypedDict classes, we need to walk the MRO to collect docstrings from
    parent classes since field annotations are merged but docstrings are not
    automatically inherited.
    
    Args:
        cls: The TypedDict class to inspect.
        use_inspect: Whether to use inspect module instead of frame inspection.
        
    Returns:
        A mapping containing attribute names and their corresponding docstring,
        with child class docstrings taking precedence over parent ones.
    """
    field_docstrings: dict[str, str] = {}
    
    # Walk the MRO in reverse order (parent to child) so child docstrings override parent ones
    for base in reversed(cls.__mro__):
        if base is cls or base is object:
            continue
            
        # Only process TypedDict bases
        from typing_extensions import is_typeddict
        if not is_typeddict(base):
            continue
            
        if use_inspect or sys.version_info >= (3, 13):
            try:
                source, _ = inspect.getsourcelines(base)
            except OSError:  # pragma: no cover
                continue
        else:
            source = _extract_source_from_frame(base)
        
        if not source:
            continue
            
        dedent_source = _dedent_source_lines(source)
        visitor = DocstringVisitor()
        visitor.visit(ast.parse(dedent_source))
        
        # Merge docstrings from this base (child values will override later)
        field_docstrings.update(visitor.attrs)
    
    # Finally extract from the class itself (this overrides any parent docstrings)
    if use_inspect or sys.version_info >= (3, 13):
        try:
            source, _ = inspect.getsourcelines(cls)
        except OSError:  # pragma: no cover
            return field_docstrings
    else:
        source = _extract_source_from_frame(cls)
    
    if not source:
        return field_docstrings
        
    dedent_source = _dedent_source_lines(source)
    visitor = DocstringVisitor()
    visitor.visit(ast.parse(dedent_source))
    field_docstrings.update(visitor.attrs)
    
    return field_docstrings
