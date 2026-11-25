# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class OutcomeTimeout(BaseModel):
    """Indicates that the shell call exceeded its configured time limit."""
    type: Literal['timeout']

class OutcomeExit(BaseModel):
    """Indicates that the shell commands finished and returned an exit code."""
    exit_code: int
    type: Literal['exit']
Outcome: TypeAlias = Annotated[Union[OutcomeTimeout, OutcomeExit], PropertyInfo(discriminator='type')]

class ResponseFunctionShellCallOutputContent(BaseModel):
    """Captured stdout and stderr for a portion of a shell tool call output."""
    outcome: Outcome
    stderr: str
    stdout: str
