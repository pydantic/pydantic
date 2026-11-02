
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .conversation_item_content import ConversationItemContent

class ConversationItem(BaseModel):
    id: Optional[str] = None
    arguments: Optional[str] = None
    call_id: Optional[str] = None
    content: Optional[List[ConversationItemContent]] = None
    name: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    output: Optional[str] = None
    role: Optional[Literal['user', 'assistant', 'system']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
    type: Optional[Literal['message', 'function_call', 'function_call_output']] = None
