# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .subagent import Subagent
from ..._models import BaseModel

class AgentSessionSubagentCreatedEvent(BaseModel):
    """Emitted when a subagent is created."""
    event_id: str
    subagent: Subagent
    type: Literal['agent.session.subagent.created']
