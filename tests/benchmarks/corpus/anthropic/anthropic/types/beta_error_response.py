
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .beta_error import BetaError

class BetaErrorResponse(BaseModel):
    error: BetaError
    request_id: Optional[str] = None
    type: Literal['error']
