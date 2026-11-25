
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class BetaRateLimitError(BaseModel):
    message: str
    type: Literal['rate_limit_error']
