# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .agent_text import AgentText
from .agent_tool import AgentTool
from .environment import Environment
from .token_usage import TokenUsage
from .agent_reasoning import AgentReasoning
from .multi_agent_config import MultiAgentConfig

class Agent(BaseModel):
    """The agent running in the session."""
    id: str
    instructions: Optional[str] = None
    model: str
    multi_agent: MultiAgentConfig
    name: Optional[str] = None
    reasoning: AgentReasoning
    service_tier: Literal['auto', 'default', 'flex', 'priority', 'fast', 'ultrafast']
    text: AgentText
    tools: List[AgentTool]

class RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthenticationField(BaseModel):
    """A control in a registered browser-login form."""
    id: str
    label: str
    required: bool
    type: str

class RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthenticationOption(BaseModel):
    """A sign-in method and the fields that belong to it."""
    id: str
    field_ids: List[str]
    label: str

class RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthentication(BaseModel):
    """A registered form awaiting the application's response."""
    credential_origin: Optional[str] = None
    fields: List[RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthenticationField]
    options: List[RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthenticationOption]
    reason: Optional[str] = None
    type: Literal['browser_authentication']

class RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserOriginAccess(BaseModel):
    """A browser origin awaiting the application's approval decision."""
    origin: str
    reason: Optional[str] = None
    type: Literal['browser_origin_access']
RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequest: TypeAlias = Annotated[Union[RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserAuthentication, RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequestComputerUseApprovalRequestKindResourceBrowserOriginAccess], PropertyInfo(discriminator='type')]

class RequiredActionSessionRequiredActionResourceComputerUseApprovalRequest(BaseModel):
    """Respond to a computer-use request."""
    request: RequiredActionSessionRequiredActionResourceComputerUseApprovalRequestRequest
    request_id: str
    turn_id: str
    type: Literal['computer_use_approval_request']

class RequiredActionSessionRequiredActionResourceFunctionCall(BaseModel):
    """Run a function tool and submit its result."""
    arguments: object
    call_id: str
    name: str
    turn_id: str
    type: Literal['function_call']

class RequiredActionSessionRequiredActionResourceEnvironmentConnection(BaseModel):
    """Reconnect a session environment."""
    environment_id: str
    type: Literal['environment_connection']
RequiredAction: TypeAlias = Annotated[Union[RequiredActionSessionRequiredActionResourceComputerUseApprovalRequest, RequiredActionSessionRequiredActionResourceFunctionCall, RequiredActionSessionRequiredActionResourceEnvironmentConnection], PropertyInfo(discriminator='type')]

class SpendControl(BaseModel):
    """Configured spending limit and best-effort consumption, in USD cents.

    Unlimited sessions omit this object.
    """
    consumed: Optional[int] = None
    limit: int

class AgentSession(BaseModel):
    """A Managed Agents session."""
    id: str
    agent: Agent
    created_at: int
    environment: Environment
    error: Optional[str] = None
    last_active_at: int
    metadata: Dict[str, str]
    object: Literal['agent.session']
    required_actions: List[RequiredAction]
    status: Literal['idle', 'in_progress', 'requires_action', 'failed']
    usage: Optional[TokenUsage] = None
    vault_ids: List[str]
    spend_control: Optional[SpendControl] = None
