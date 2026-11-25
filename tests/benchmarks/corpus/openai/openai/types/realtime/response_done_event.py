# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_response import RealtimeResponse

class ResponseDoneEvent(BaseModel):
    """Returned when a Response is done streaming.

    Always emitted, no matter the
    final state. The Response object included in the `response.done` event will
    include all output Items in the Response but will omit the raw audio data.

    Clients should check the `status` field of the Response to determine if it was successful
    (`completed`) or if there was another outcome: `cancelled`, `failed`, or `incomplete`.

    A response will contain all output items that were generated during the response, excluding
    any audio content.
    """
    event_id: str
    response: RealtimeResponse
    type: Literal['response.done']
