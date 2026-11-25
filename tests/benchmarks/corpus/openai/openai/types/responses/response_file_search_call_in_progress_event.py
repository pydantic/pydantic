# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseFileSearchCallInProgressEvent(BaseModel):
    """Emitted when a file search call is initiated."""
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.file_search_call.in_progress']
