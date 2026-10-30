
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.error_response import ErrorResponse

class MessageBatchErroredResult(BaseModel):
    error: ErrorResponse
    type: Literal['errored']
