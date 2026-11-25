# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ...._models import BaseModel
from .message_content import MessageContent
from ...shared.metadata import Metadata
from ..code_interpreter_tool import CodeInterpreterTool

class AttachmentToolAssistantToolsFileSearchTypeOnly(BaseModel):
    type: Literal['file_search']
AttachmentTool: TypeAlias = Union[CodeInterpreterTool, AttachmentToolAssistantToolsFileSearchTypeOnly]

class Attachment(BaseModel):
    file_id: Optional[str] = None
    tools: Optional[List[AttachmentTool]] = None

class IncompleteDetails(BaseModel):
    """On an incomplete message, details about why the message is incomplete."""
    reason: Literal['content_filter', 'max_tokens', 'run_cancelled', 'run_expired', 'run_failed']

class Message(BaseModel):
    """
    Represents a message within a [thread](https://developers.openai.com/api/docs/assistants/migration).
    """
    id: str
    assistant_id: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    completed_at: Optional[int] = None
    content: List[MessageContent]
    created_at: int
    incomplete_at: Optional[int] = None
    incomplete_details: Optional[IncompleteDetails] = None
    metadata: Optional[Metadata] = None
    object: Literal['thread.message']
    role: Literal['user', 'assistant']
    run_id: Optional[str] = None
    status: Literal['in_progress', 'incomplete', 'completed']
    thread_id: str
