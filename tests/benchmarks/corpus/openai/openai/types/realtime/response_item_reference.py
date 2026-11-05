# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseItemReference(BaseModel):
    """
    Reference an existing item in this Realtime session as response.create input.
    Item references are only accepted in the response input array, not as new
    conversation items.
    """
    id: str
    type: Literal['item_reference']
