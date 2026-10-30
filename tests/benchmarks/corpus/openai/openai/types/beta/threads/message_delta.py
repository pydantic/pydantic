# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .message_content_delta import MessageContentDelta

class MessageDelta(BaseModel):
    """The delta containing the fields that have changed on the Message."""
    content: Optional[List[MessageContentDelta]] = None
    role: Optional[Literal['user', 'assistant']] = None
