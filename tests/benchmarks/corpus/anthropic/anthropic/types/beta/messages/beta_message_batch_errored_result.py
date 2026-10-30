
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from ...beta_error_response import BetaErrorResponse

class BetaMessageBatchErroredResult(BaseModel):
    error: BetaErrorResponse
    type: Literal['errored']
