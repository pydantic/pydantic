# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel
from ..beta_response_item import BetaResponseItem

class BetaResponseItemList(BaseModel):
    """A list of Response items."""
    data: List[BetaResponseItem]
    first_id: str
    has_more: bool
    last_id: str
    object: Literal['list']
