# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseCustomToolCallInputDoneEvent(BaseModel):
    """Event indicating that input for a custom tool call is complete."""
    input: str
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.custom_tool_call_input.done']
