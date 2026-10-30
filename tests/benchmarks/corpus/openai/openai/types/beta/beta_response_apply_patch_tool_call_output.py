# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class BetaResponseApplyPatchToolCallOutput(BaseModel):
    """The output emitted by an apply patch tool call."""
    id: str
    call_id: str
    status: Literal['completed', 'failed']
    type: Literal['apply_patch_call_output']
    agent: Optional[Agent] = None
    caller: Optional[Caller] = None
    created_by: Optional[str] = None
    output: Optional[str] = None
