
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..message import Message
from ..._models import BaseModel

class MessageBatchSucceededResult(BaseModel):
    message: Message
    type: Literal['succeeded']
