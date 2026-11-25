
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaAdvisorResultBlock(BaseModel):
    stop_reason: Optional[str] = None
    text: str
    type: Literal['advisor_result']
