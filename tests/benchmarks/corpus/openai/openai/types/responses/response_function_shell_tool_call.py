# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .response_local_environment import ResponseLocalEnvironment
from .response_container_reference import ResponseContainerReference

class Action(BaseModel):
    """The shell commands and limits that describe how to run the tool call."""
    commands: List[str]
    max_output_length: Optional[int] = None
    timeout_ms: Optional[int] = None
Environment: TypeAlias = Annotated[Union[ResponseLocalEnvironment, ResponseContainerReference, None], PropertyInfo(discriminator='type')]

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseFunctionShellToolCall(BaseModel):
    """A tool call that executes one or more shell commands in a managed environment."""
    id: str
    action: Action
    call_id: str
    environment: Optional[Environment] = None
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['shell_call']
    caller: Optional[Caller] = None
    created_by: Optional[str] = None
