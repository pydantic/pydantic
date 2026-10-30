# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseFunctionCallArgumentsDeltaEvent(BaseModel):
    """Emitted when there is a partial function-call arguments delta."""
    delta: str
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.function_call_arguments.delta']
