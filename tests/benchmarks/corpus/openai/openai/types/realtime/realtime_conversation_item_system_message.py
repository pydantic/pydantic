# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Content(BaseModel):
    text: Optional[str] = None
    type: Optional[Literal['input_text']] = None

class RealtimeConversationItemSystemMessage(BaseModel):
    """
    A system message in a Realtime conversation can be used to provide additional context or instructions to the model. This is similar but distinct from the instruction prompt provided at the start of a conversation, as system messages can be added at any point in the conversation. For major changes to the conversation's behavior, use instructions, but for smaller updates (e.g. "the user is now asking about a different topic"), use system messages.
    """
    content: List[Content]
    role: Literal['system']
    type: Literal['message']
    id: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
