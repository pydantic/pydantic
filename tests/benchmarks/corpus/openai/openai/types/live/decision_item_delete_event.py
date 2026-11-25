# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class DecisionItemDeleteEvent(BaseModel):
    """
    Delete an input item from future decisions without starting an evaluation or changing Live voice context.
    """
    item_id: str
    type: Literal['decision.item.delete']
    event_id: Optional[str] = None
