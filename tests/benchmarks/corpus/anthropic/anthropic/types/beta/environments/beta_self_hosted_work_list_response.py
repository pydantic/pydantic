
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ...._models import BaseModel
from .beta_self_hosted_work import BetaSelfHostedWork

class BetaSelfHostedWorkListResponse(BaseModel):
    """Response when listing work items with cursor-based pagination."""
    data: List[BetaSelfHostedWork]
    next_page: Optional[str] = None
