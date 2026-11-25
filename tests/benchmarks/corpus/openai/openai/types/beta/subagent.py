# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_content import AgentContent

class Subagent(BaseModel):
    """A subagent created within a session."""
    id: str
    closed_at: Optional[int] = None
    instructions: Optional[List[AgentContent]] = None
    name: Optional[str] = None
    object: Literal['agent.session.subagent']
    opened_at: int
    parent_agent_id: str
    session_id: str
    status: Literal['active', 'closed']
