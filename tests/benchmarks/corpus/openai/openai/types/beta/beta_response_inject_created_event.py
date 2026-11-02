# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaResponseInjectCreatedEvent(BaseModel):
    """
    Emitted when all injected input items were validated and committed to the
    active response.
    """
    response_id: str
    sequence_number: int
    type: Literal['response.inject.created']
    stream_id: Optional[str] = None
