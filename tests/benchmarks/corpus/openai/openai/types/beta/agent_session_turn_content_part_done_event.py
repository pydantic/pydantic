# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .output_text import OutputText

class AgentSessionTurnContentPartDoneEvent(BaseModel):
    """Emitted when an output content part is complete."""
    content_index: int
    event_id: str
    item_id: str
    output_index: int
    part: OutputText
    session_id: str
    turn_id: Optional[str] = None
    type: Literal['agent.session.turn.content_part.done']
