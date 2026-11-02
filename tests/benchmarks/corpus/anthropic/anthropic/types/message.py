
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .model import Model
from .usage import Usage
from .._models import BaseModel
from .container import Container
from .diagnostics import Diagnostics
from .stop_reason import StopReason
from .content_block import ContentBlock, ContentBlock as ContentBlock
from .refusal_stop_details import RefusalStopDetails

class Message(BaseModel):
    id: str
    container: Optional[Container] = None
    content: List[ContentBlock]
    diagnostics: Optional[Diagnostics] = None
    model: Model
    role: Literal['assistant']
    stop_details: Optional[RefusalStopDetails] = None
    stop_reason: Optional[StopReason] = None
    stop_sequence: Optional[str] = None
    type: Literal['message']
    usage: Usage
