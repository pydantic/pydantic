
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Error(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None

class RealtimeResponseStatus(BaseModel):
    error: Optional[Error] = None
    reason: Optional[Literal['turn_detected', 'client_cancelled', 'max_output_tokens', 'content_filter']] = None
    type: Optional[Literal['completed', 'cancelled', 'incomplete', 'failed']] = None
