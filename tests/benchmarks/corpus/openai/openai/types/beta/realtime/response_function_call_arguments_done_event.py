
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class ResponseFunctionCallArgumentsDoneEvent(BaseModel):
    arguments: str
    call_id: str
    event_id: str
    item_id: str
    output_index: int
    response_id: str
    type: Literal['response.function_call_arguments.done']
