# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseReasoningSummaryTextDeltaEvent(BaseModel):
    """Emitted when a delta is added to a reasoning summary text."""
    delta: str
    item_id: str
    output_index: int
    sequence_number: int
    summary_index: int
    type: Literal['response.reasoning_summary_text.delta']
