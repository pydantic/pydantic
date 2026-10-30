# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel
from ..input_content import InputContent
from .automation_environment import AutomationEnvironment
from .automation_agent_config import AutomationAgentConfig

class AutomationTargetResourceNewSessionInput(BaseModel):
    """A user message recorded in a session."""
    content: List[InputContent]
    role: Literal['user']
    type: Literal['message']

class AutomationTargetResourceNewSession(BaseModel):
    agent: Optional[AutomationAgentConfig] = None
    agent_id: Optional[str] = None
    environment: AutomationEnvironment
    input: List[AutomationTargetResourceNewSessionInput]
    metadata: Dict[str, str]
    type: Literal['new_session']
    vault_ids: List[str]

class AutomationTargetResourceExistingSession(BaseModel):
    instructions: str
    session_id: str
    type: Literal['existing_session']
AutomationTarget: TypeAlias = Annotated[Union[AutomationTargetResourceNewSession, AutomationTargetResourceExistingSession], PropertyInfo(discriminator='type')]
