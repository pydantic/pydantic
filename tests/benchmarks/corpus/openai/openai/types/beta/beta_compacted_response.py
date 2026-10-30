# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_usage import BetaResponseUsage
from .beta_response_output_item import BetaResponseOutputItem

class BetaCompactedResponse(BaseModel):
    id: str
    created_at: int
    object: Literal['response.compaction']
    output: List[BetaResponseOutputItem]
    usage: BetaResponseUsage
