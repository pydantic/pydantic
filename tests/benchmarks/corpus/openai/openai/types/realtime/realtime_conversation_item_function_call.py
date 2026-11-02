# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeConversationItemFunctionCall(BaseModel):
    """A function call item in a Realtime conversation."""
    arguments: str
    name: str
    type: Literal['function_call']
    id: Optional[str] = None
    call_id: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
