# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class AgentSessionTurnOutputTextDeltaEvent(BaseModel):
    """Emitted when text is appended to an output text content part."""
    content_index: int
    delta: str
    event_id: str
    item_id: str
    output_index: int
    session_id: str
    turn_id: Optional[str] = None
    type: Literal['agent.session.turn.output_text.delta']
