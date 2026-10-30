
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_dream_error import BetaDreamError
from .beta_dream_input import BetaDreamInput
from .beta_dream_usage import BetaDreamUsage
from .beta_dream_output import BetaDreamOutput
from .beta_dream_status import BetaDreamStatus
from .beta_output_behavior import BetaOutputBehavior
from .beta_dream_model_config import BetaDreamModelConfig

class BetaDream(BaseModel):
    """
    An asynchronous job that reads a memory store and past sessions, then writes a reorganized version of that memory store.

    By default the dream writes its result to a new memory store and doesn't change the input memory store. With `output_behavior` set to `update_existing`, it writes its result into the input memory store instead.

    The Dreams API is in research preview: the request and response shapes are volatile and may change without the deprecation period that applies to generally-available endpoints.

    See the [Dreams guide](https://platform.claude.com/docs/en/managed-agents/dreams#how-it-works) for what a dream reads and produces.
    """
    id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    ended_at: Optional[datetime] = None
    error: Optional[BetaDreamError] = None
    inputs: List[BetaDreamInput]
    instructions: Optional[str] = None
    model: BetaDreamModelConfig
    output_behavior: BetaOutputBehavior
    outputs: List[BetaDreamOutput]
    session_id: Optional[str] = None
    status: BetaDreamStatus
    type: Literal['dream']
    usage: BetaDreamUsage
