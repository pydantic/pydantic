# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel
from .chatkit_attachment import ChatKitAttachment

class ContentInputText(BaseModel):
    """Text block that a user contributed to the thread."""
    text: str
    type: Literal['input_text']

class ContentQuotedText(BaseModel):
    """Quoted snippet that the user referenced in their message."""
    text: str
    type: Literal['quoted_text']
Content: TypeAlias = Annotated[Union[ContentInputText, ContentQuotedText], PropertyInfo(discriminator='type')]

class InferenceOptionsToolChoice(BaseModel):
    """Preferred tool to invoke. Defaults to null when ChatKit should auto-select."""
    id: str

class InferenceOptions(BaseModel):
    """Inference overrides applied to the message. Defaults to null when unset."""
    model: Optional[str] = None
    tool_choice: Optional[InferenceOptionsToolChoice] = None

class ChatKitThreadUserMessageItem(BaseModel):
    """User-authored messages within a thread."""
    id: str
    attachments: List[ChatKitAttachment]
    content: List[Content]
    created_at: int
    inference_options: Optional[InferenceOptions] = None
    object: Literal['chatkit.thread_item']
    thread_id: str
    type: Literal['chatkit.user_message']
