# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeConversationItemFunctionCallOutput(BaseModel):
    """A function call output item in a Realtime conversation."""
    call_id: str
    output: str
    type: Literal['function_call_output']
    id: Optional[str] = None
    object: Optional[Literal['realtime.item']] = None
    status: Optional[Literal['completed', 'incomplete', 'in_progress']] = None
