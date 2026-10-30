
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_message import BetaMessage

class BetaRawMessageStartEvent(BaseModel):
    message: BetaMessage
    type: Literal['message_start']
