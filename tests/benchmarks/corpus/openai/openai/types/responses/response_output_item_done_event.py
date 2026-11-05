# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .response_output_item import ResponseOutputItem

class ResponseOutputItemDoneEvent(BaseModel):
    """Emitted when an output item is marked done."""
    item: ResponseOutputItem
    output_index: int
    sequence_number: int
    type: Literal['response.output_item.done']
