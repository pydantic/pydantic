# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class OperationCreateFile(BaseModel):
    """Instruction describing how to create a file via the apply_patch tool."""
    diff: str
    path: str
    type: Literal['create_file']

class OperationDeleteFile(BaseModel):
    """Instruction describing how to delete a file via the apply_patch tool."""
    path: str
    type: Literal['delete_file']

class OperationUpdateFile(BaseModel):
    """Instruction describing how to update a file via the apply_patch tool."""
    diff: str
    path: str
    type: Literal['update_file']
Operation: TypeAlias = Annotated[Union[OperationCreateFile, OperationDeleteFile, OperationUpdateFile], PropertyInfo(discriminator='type')]

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseApplyPatchToolCall(BaseModel):
    """A tool call that applies file diffs by creating, deleting, or updating files."""
    id: str
    call_id: str
    operation: Operation
    status: Literal['in_progress', 'completed']
    type: Literal['apply_patch_call']
    caller: Optional[Caller] = None
    created_by: Optional[str] = None
