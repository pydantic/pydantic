
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class ResponseTextDeltaEvent(BaseModel):
    content_index: int
    delta: str
    event_id: str
    item_id: str
    output_index: int
    response_id: str
    type: Literal['response.text.delta']
