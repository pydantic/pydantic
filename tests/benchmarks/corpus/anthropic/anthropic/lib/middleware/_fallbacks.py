
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..._models import BaseModel

class _Refusal(BaseModel):
    token: Optional[str]
    category: Optional[str]
    has_prefill_claim: bool
    usage: Dict[str, Any]
    event: Dict[str, Any]
    suppressed_start_message: Optional[Dict[str, Any]] = None

class _SpliceInfo(BaseModel):
    """Splice context for fallback hops; `None` for stream A."""
    iterations: List[Dict[str, Any]]
    model: str

class _HopFailure(BaseModel):
    """A fallback hop whose request failed; stamps `recommended_model` when it
    ends the chain."""
    model: str
    status: Optional[int]

class _HopOutcome(BaseModel):
    """The outcome of consuming one hop's stream."""
    refused: Optional[_Refusal]
    model: Optional[str]
    start_event: Optional[Dict[str, Any]]
    blocks: List[Dict[str, Any]]
    next_index: int
    opened: bool
    last_fallback_to: Optional[str]
