
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_managed_agents_agent_message_preview import BetaManagedAgentsAgentMessagePreview
from .beta_managed_agents_agent_thinking_preview import BetaManagedAgentsAgentThinkingPreview
BetaManagedAgentsStartEventPreview: TypeAlias = Annotated[Union[BetaManagedAgentsAgentMessagePreview, BetaManagedAgentsAgentThinkingPreview], UnionDiscriminator('type')]
