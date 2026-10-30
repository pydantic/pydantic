# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Delegation(BaseModel):
    """The delegated work identifier and destination.

    This object contains metadata, not the task text.
    """
    id: str
    target: Literal['client', 'responses', 'decisions']
    type: Literal['delegation']
    response_id: Optional[str] = None

class DelegationCreatedEvent(BaseModel):
    """
    Returned when the Live model delegates work to your application, Responses, or Decisions. Contains delegation metadata and the position on the session timeline where the work was delegated.
    """
    delegation: Delegation
    event_id: str
    offset_ms: int
    type: Literal['session.delegation.created']
    client_event_id: Optional[str] = None
