# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, TypeAlias
Operator = Literal['', '+', '#', '.', '/', ';', '?', '&']

@dataclass(frozen=True)
class Variable:
    name: str
    operator: Operator
    explode: bool = False

@dataclass
class _Expression:
    operator: Operator
    variables: list[Variable]
_Part = str | _Expression

@dataclass(frozen=True)
class _Lit:
    text: str

@dataclass(frozen=True)
class _Cap:
    var: Variable
    ifemp: bool = False
_Atom: TypeAlias = _Lit | _Cap

@dataclass(frozen=True)
class UriTemplate:
    template: str
    _parts: list[_Part] = field(repr=False, compare=False)
    _variables: list[Variable] = field(repr=False, compare=False)
    _prefix: list[_Atom] = field(repr=False, compare=False)
    _greedy: Variable | None = field(repr=False, compare=False)
    _suffix: list[_Atom] = field(repr=False, compare=False)
    _query_variables: list[Variable] = field(repr=False, compare=False)
