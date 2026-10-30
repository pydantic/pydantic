
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from ..beta_managed_agents_custom_tool import BetaManagedAgentsCustomTool
from ..beta_managed_agents_mcp_toolset import BetaManagedAgentsMCPToolset
from ..beta_managed_agents_custom_skill import BetaManagedAgentsCustomSkill
from ..beta_managed_agents_model_config import BetaManagedAgentsModelConfig
from ..beta_managed_agents_anthropic_skill import BetaManagedAgentsAnthropicSkill
from ..beta_managed_agents_execution_identity import BetaManagedAgentsExecutionIdentity
from ..beta_managed_agents_agent_toolset20260401 import BetaManagedAgentsAgentToolset20260401
from ..beta_managed_agents_mcp_server_url_definition import BetaManagedAgentsMCPServerURLDefinition
Skill: TypeAlias = Annotated[Union[BetaManagedAgentsAnthropicSkill, BetaManagedAgentsCustomSkill], UnionDiscriminator('type')]
Tool: TypeAlias = Annotated[Union[BetaManagedAgentsAgentToolset20260401, BetaManagedAgentsMCPToolset, BetaManagedAgentsCustomTool], UnionDiscriminator('type')]

class BetaManagedAgentsInlineAgent(BaseModel):
    """An agent that has no Agent resource, and so no `id` or `version`.

    It is defined inline, in a workflow run's plan or when a session thread is spawned, and is not saved.
    """
    description: Optional[str] = None
    execution_identity: BetaManagedAgentsExecutionIdentity
    mcp_servers: List[BetaManagedAgentsMCPServerURLDefinition]
    model: BetaManagedAgentsModelConfig
    name: str
    skills: List[Skill]
    system: Optional[str] = None
    tools: List[Tool]
    type: Literal['inline']
