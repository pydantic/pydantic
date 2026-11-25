# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel
from .chatkit_response_output_text import ChatKitResponseOutputText

class ChatKitThreadAssistantMessageItem(BaseModel):
    """Assistant-authored message within a thread."""
    id: str
    content: List[ChatKitResponseOutputText]
    created_at: int
    object: Literal['chatkit.thread_item']
    thread_id: str
    type: Literal['chatkit.assistant_message']
