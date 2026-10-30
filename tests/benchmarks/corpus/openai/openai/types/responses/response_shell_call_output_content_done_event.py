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

class ResponseShellCallOutputContentDoneEvent(BaseModel):
    """A streaming event that indicated shell call output was completed."""
    command_index: int
    item_id: str
    output: List[Output]
    output_index: int
    sequence_number: int
    type: Literal['response.shell_call_output_content.done']
