# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_text import AgentText
from .agent_reasoning import AgentReasoning
from .multi_agent_config import MultiAgentConfig
from .persisted_agent_tool import PersistedAgentTool

class Agent(BaseModel):
    """A reusable agent scoped to the caller's project."""
    id: str
    created_at: int
    instructions: Optional[str] = None
    metadata: Dict[str, str]
    model: str
    multi_agent: MultiAgentConfig
    name: Optional[str] = None
    object: Literal['agent']
    reasoning: AgentReasoning
    service_tier: Literal['auto', 'default', 'flex', 'priority', 'fast', 'ultrafast']
    text: AgentText
    tools: List[PersistedAgentTool]
    updated_at: int
