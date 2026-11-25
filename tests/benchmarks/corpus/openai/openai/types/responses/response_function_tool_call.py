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

class ResponseFunctionToolCall(BaseModel):
    """A tool call to run a function.

    See the
    [function calling guide](https://developers.openai.com/api/docs/guides/function-calling) for more information.
    """
    arguments: str
    call_id: str
    name: str
    type: Literal['function_call']
    id: Optional[str] = None
    async_: Optional[bool] = FieldInfo(alias='async', default=None)
    caller: Optional[Caller] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
