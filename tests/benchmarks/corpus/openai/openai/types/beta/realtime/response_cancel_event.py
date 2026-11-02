
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ResponseCancelEvent(BaseModel):
    type: Literal['response.cancel']
    event_id: Optional[str] = None
    response_id: Optional[str] = None
