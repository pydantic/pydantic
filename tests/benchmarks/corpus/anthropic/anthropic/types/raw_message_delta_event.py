
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .container import Container
from .stop_reason import StopReason
from .message_delta_usage import MessageDeltaUsage
from .refusal_stop_details import RefusalStopDetails

class Delta(BaseModel):
    container: Optional[Container] = None
    stop_details: Optional[RefusalStopDetails] = None
    stop_reason: Optional[StopReason] = None
    stop_sequence: Optional[str] = None

class RawMessageDeltaEvent(BaseModel):
    delta: Delta
    type: Literal['message_delta']
    usage: MessageDeltaUsage
