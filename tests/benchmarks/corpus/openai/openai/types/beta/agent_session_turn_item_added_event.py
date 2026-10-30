# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_session_item import AgentSessionItem

class AgentSessionTurnItemAddedEvent(BaseModel):
    """Emitted when an item is added to a turn."""
    event_id: str
    item: AgentSessionItem
    output_index: Optional[int] = None
    session_id: str
    turn_id: Optional[str] = None
    type: Literal['agent.session.turn.item.added']
