# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from ..._utils import PropertyInfo
from ..._models import BaseModel

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseCustomToolCall(BaseModel):
    """A call to a custom tool created by the model."""
    call_id: str
    input: str
    name: str
    type: Literal['custom_tool_call']
    id: Optional[str] = None
    async_: Optional[bool] = FieldInfo(alias='async', default=None)
    caller: Optional[Caller] = None
    namespace: Optional[str] = None
