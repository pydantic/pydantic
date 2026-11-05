# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .agent_mcp_call_item import AgentMcpCallItem
from .agent_reasoning_item import AgentReasoningItem
from .agent_function_call_item import AgentFunctionCallItem
from .agent_function_call_status import AgentFunctionCallStatus
from .agent_web_search_call_item import AgentWebSearchCallItem
from .agent_command_execution_item import AgentCommandExecutionItem
from .agent_close_subagent_call_item import AgentCloseSubagentCallItem
from .agent_create_subagent_call_item import AgentCreateSubagentCallItem
from .agent_resume_subagent_call_item import AgentResumeSubagentCallItem
from .agent_session_assistant_message import AgentSessionAssistantMessage
from .agent_interrupt_subagent_call_item import AgentInterruptSubagentCallItem
from .agent_wait_for_subagents_call_item import AgentWaitForSubagentsCallItem
from .agent_send_subagent_input_call_item import AgentSendSubagentInputCallItem

class ComputerUseCallItemResourceOutput(BaseModel):
    """The last screenshot emitted by the model.

    Null when screenshot inclusion is disabled or the call emitted no screenshot.
    """
    image_url: str
    type: Literal['computer_screenshot']

class ComputerUseCallItemResource(BaseModel):
    """One execution of the platform-provided computer-use capability."""
    id: str
    output: Optional[ComputerUseCallItemResourceOutput] = None
    status: AgentFunctionCallStatus
    title: Optional[str] = None
    turn_id: str
    type: Literal['computer_use_call']

class BrowserAuthenticationRequestItemResourceRequestField(BaseModel):
    """A control in a registered browser-login form."""
    id: str
    label: str
    required: bool
    type: str

class BrowserAuthenticationRequestItemResourceRequestOption(BaseModel):
    """A sign-in method and the fields that belong to it."""
    id: str
    field_ids: List[str]
    label: str

class BrowserAuthenticationRequestItemResourceRequest(BaseModel):
    """A registered form awaiting the application's response."""
    credential_origin: Optional[str] = None
    fields: List[BrowserAuthenticationRequestItemResourceRequestField]
    options: List[BrowserAuthenticationRequestItemResourceRequestOption]
    reason: Optional[str] = None
    type: Literal['browser_authentication']

class BrowserAuthenticationRequestItemResource(BaseModel):
    """A credential-free history record of the emitted login request."""
    id: str
    request: BrowserAuthenticationRequestItemResourceRequest
    request_id: str
    turn_id: str
    type: Literal['computer_use_approval_request']
AgentOutputItem: TypeAlias = Annotated[Union[AgentSessionAssistantMessage, AgentReasoningItem, AgentFunctionCallItem, AgentMcpCallItem, ComputerUseCallItemResource, BrowserAuthenticationRequestItemResource, AgentWebSearchCallItem, AgentCommandExecutionItem, AgentCreateSubagentCallItem, AgentSendSubagentInputCallItem, AgentResumeSubagentCallItem, AgentWaitForSubagentsCallItem, AgentInterruptSubagentCallItem, AgentCloseSubagentCallItem], PropertyInfo(discriminator='type')]
