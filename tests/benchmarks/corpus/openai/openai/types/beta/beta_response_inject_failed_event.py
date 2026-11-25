# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_input_item import BetaResponseInputItem

class Error(BaseModel):
    """Information about why the input was not committed."""
    code: Literal['response_already_completed', 'response_not_found']
    message: str

class BetaResponseInjectFailedEvent(BaseModel):
    """Emitted when injected input could not be committed to a response.

    The event
    returns the uncommitted raw input so the client can retry it in another
    response when appropriate.
    """
    error: Error
    input: List[BetaResponseInputItem]
    response_id: str
    sequence_number: int
    type: Literal['response.inject.failed']
    stream_id: Optional[str] = None
