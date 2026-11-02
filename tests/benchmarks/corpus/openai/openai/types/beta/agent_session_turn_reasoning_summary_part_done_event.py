# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .summary_text import SummaryText

class AgentSessionTurnReasoningSummaryPartDoneEvent(BaseModel):
    """Emitted when a reasoning summary part is complete."""
    event_id: str
    item_id: str
    output_index: int
    part: SummaryText
    session_id: str
    status: Optional[Literal['incomplete']] = None
    summary_index: int
    turn_id: Optional[str] = None
    type: Literal['agent.session.turn.reasoning_summary_part.done']
