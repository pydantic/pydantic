# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .response_steer_pending_reason import ResponseSteerPendingReason
from .response_steer_required_input import ResponseSteerRequiredInput

class Steer(BaseModel):
    """The steering submission that remains queued."""
    id: str
    previous_response_id: str

class ResponseSteerPendingEvent(BaseModel):
    """
    Emitted when accepted steering input remains queued after the target
    response completes. The server still owns the input. Do not resend it.
    The successor's `response.created` event is the commit point.

    When `reason` is `waiting_for_required_input`, this event follows
    `response.completed` while the response waits for the tool results or
    approval decisions identified by `required_input`. Copy those stubs, fill
    their result fields using the ordinary `response.create` input schemas,
    and submit one continuation per parent with the same `previous_response_id`
    and WebSocket lane. Use saved results without rerunning tools. The queued
    steering input is prepended in submission order to the continuation's
    input. That explicit request retains its own settings.

    This notification is emitted at most once per steering submission. Multiple
    submissions for the same parent can report the same required inputs; they
    do not each require a separate continuation.
    """
    reason: ResponseSteerPendingReason
    required_input: List[ResponseSteerRequiredInput]
    sequence_number: int
    steer: Steer
    type: Literal['response.steer.pending']
    stream_id: Optional[str] = None
