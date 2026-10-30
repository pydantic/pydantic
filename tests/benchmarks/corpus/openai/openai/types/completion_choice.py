# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from .._models import BaseModel

class Logprobs(BaseModel):
    text_offset: Optional[List[int]] = None
    token_logprobs: Optional[List[float]] = None
    tokens: Optional[List[str]] = None
    top_logprobs: Optional[List[Dict[str, float]]] = None

class CompletionChoice(BaseModel):
    finish_reason: Literal['stop', 'length', 'content_filter']
    index: int
    logprobs: Optional[Logprobs] = None
    text: str
