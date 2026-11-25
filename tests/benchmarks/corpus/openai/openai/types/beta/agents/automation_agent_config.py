# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from ..agent_text import AgentText
from ..agent_tool import AgentTool
from ..agent_reasoning import AgentReasoning
from ..multi_agent_config import MultiAgentConfig

class AutomationAgentConfig(BaseModel):
    """Inline agent configuration without a generated session-local identity."""
    instructions: Optional[str] = None
    model: str
    multi_agent: MultiAgentConfig
    reasoning: AgentReasoning
    service_tier: Literal['auto', 'default', 'flex', 'priority', 'fast', 'ultrafast']
    text: AgentText
    tools: List[AgentTool]
