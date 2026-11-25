# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseFileSearchCallSearchingEvent(BaseModel):
    """Emitted when a file search is currently searching."""
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.file_search_call.searching']
