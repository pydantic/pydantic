# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseCompactionCompactingEvent(BaseModel):
    """Emitted when new summary content is sampled for a compaction trigger.

    Contains no summary content.
    """
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.compaction.compacting']
    agent: Optional[Agent] = None
