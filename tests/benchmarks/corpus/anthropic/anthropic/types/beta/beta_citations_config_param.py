
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaCitationsConfigParam(BaseModel):
    enabled: Optional[bool] = None
