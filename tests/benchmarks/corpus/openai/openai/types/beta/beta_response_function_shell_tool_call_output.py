# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class OutputOutcomeTimeout(BaseModel):
    """Indicates that the shell call exceeded its configured time limit."""
    type: Literal['timeout']

class OutputOutcomeExit(BaseModel):
    """Indicates that the shell commands finished and returned an exit code."""
    exit_code: int
    type: Literal['exit']
OutputOutcome: TypeAlias = Annotated[Union[OutputOutcomeTimeout, OutputOutcomeExit], PropertyInfo(discriminator='type')]

class Output(BaseModel):
    """The content of a shell tool call output that was emitted."""
    outcome: OutputOutcome
    stderr: str
    stdout: str
    created_by: Optional[str] = None

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class BetaResponseFunctionShellToolCallOutput(BaseModel):
    """The output of a shell tool call that was emitted."""
    id: str
    call_id: str
    max_output_length: Optional[int] = None
    output: List[Output]
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['shell_call_output']
    agent: Optional[Agent] = None
    caller: Optional[Caller] = None
    created_by: Optional[str] = None
