# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseFunctionCallArgumentsDoneEvent(BaseModel):
    """
    Returned when the model-generated function call arguments are done streaming.
    Also emitted when a Response is interrupted, incomplete, or cancelled.
    """
    arguments: str
    call_id: str
    event_id: str
    item_id: str
    name: str
    output_index: int
    response_id: str
    type: Literal['response.function_call_arguments.done']
