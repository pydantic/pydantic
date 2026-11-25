# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .message_delta import MessageDelta

class MessageDeltaEvent(BaseModel):
    """Represents a message delta i.e.

    any changed fields on a message during streaming.
    """
    id: str
    delta: MessageDelta
    object: Literal['thread.message.delta']
