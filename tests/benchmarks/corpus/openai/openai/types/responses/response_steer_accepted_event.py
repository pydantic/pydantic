# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Steer(BaseModel):
    """The accepted steering submission."""
    id: str
    previous_response_id: str

class ResponseSteerAcceptedEvent(BaseModel):
    """Emitted when steering input has been validated and queued.

    Acceptance means
    the server owns the input, not that it has been applied. The successor's
    `response.created` event is the commit point. If accepted input cannot be
    committed, `response.steer.failed` returns it with the same steering ID.

    When the response stops for client-owned tool output or approval, the input
    remains queued and `response.steer.pending` is emitted after
    `response.completed`. Fill the pending event's `required_input` stubs with
    saved results and send one matching explicit `response.create` per parent.
    Do not resend accepted input while it is still queued.
    """
    sequence_number: int
    steer: Steer
    type: Literal['response.steer.accepted']
    stream_id: Optional[str] = None
