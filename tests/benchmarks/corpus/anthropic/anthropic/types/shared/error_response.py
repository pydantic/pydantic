
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .error_object import ErrorObject

class ErrorResponse(BaseModel):
    error: ErrorObject
    request_id: Optional[str] = None
    type: Literal['error']
