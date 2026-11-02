# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_steer_input import BetaResponseSteerInput

class BetaResponseSteerEvent(BaseModel):
    """Queues user input to steer a response on this WebSocket connection.

    Input
    can contain text, images, and files. Steering is supported only for
    single-agent responses on models and execution modes that support steering.
    Responses bound to a conversation or using automatic compaction do not
    support steering.

    A `response.steer.accepted` event acknowledges that the server owns the
    queued input, not that it has been applied. The successor's `response.created`
    event is the commit point. Input that cannot be committed is returned in
    `response.steer.failed`.

    Steering may cause the active response to finish at a safe output boundary
    with `response.incomplete` and `incomplete_details.reason` set to `steered`,
    followed automatically by a successor `response.created`. Normal completion
    can also be followed by an automatic successor. Automatic successors inherit
    the previous response's settings and continue from it with the queued input.

    If the response stops for client-owned tool output or approval, accepted
    steering input remains queued and `response.steer.pending` is emitted after
    `response.completed`. Fill the `required_input` stubs from that event with
    saved tool results or approval decisions, and send one explicit
    `response.create` per parent with the same `previous_response_id` and
    WebSocket lane. Do not rerun tools or resend accepted steering input. The
    queued input is prepended in submission order to that request's input, and
    the explicit request retains its own settings.

    This event accepts only `type`, `previous_response_id`, and `input`. Do not
    send `stream_id`; the target response determines the WebSocket lane.
    """
    input: BetaResponseSteerInput
    previous_response_id: str
    type: Literal['response.steer']
