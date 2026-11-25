# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..responses.response_input_item import ResponseInputItem

class ResponseItemCreateEvent(BaseModel):
    """Add an input item to the Live session’s Responses backend.

    Requires Responses delegation; use `response.create` to request a response.
    """
    item: ResponseInputItem
    type: Literal['response.item.create']
    event_id: Optional[str] = None
