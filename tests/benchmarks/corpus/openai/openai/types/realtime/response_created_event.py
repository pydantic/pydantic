# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_response import RealtimeResponse

class ResponseCreatedEvent(BaseModel):
    """Returned when a new Response is created.

    The first event of response creation,
    where the response is in an initial state of `in_progress`.
    """
    event_id: str
    response: RealtimeResponse
    type: Literal['response.created']
