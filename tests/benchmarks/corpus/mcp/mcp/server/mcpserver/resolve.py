# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel

class _StateEntry(BaseModel):
    action: Literal['accept', 'decline', 'cancel']
    data: Any = None
    q: str | None = None

class _State(BaseModel):
    v: int
    outcomes: dict[str, _StateEntry] = {}
    asked: dict[str, str] = {}
