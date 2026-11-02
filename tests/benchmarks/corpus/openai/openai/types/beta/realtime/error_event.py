
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Error(BaseModel):
    message: str
    type: str
    code: Optional[str] = None
    event_id: Optional[str] = None
    param: Optional[str] = None

class ErrorEvent(BaseModel):
    error: Error
    event_id: str
    type: Literal['error']
