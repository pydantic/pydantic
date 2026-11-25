
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .realtime_response import RealtimeResponse

class ResponseCreatedEvent(BaseModel):
    event_id: str
    response: RealtimeResponse
    type: Literal['response.created']
