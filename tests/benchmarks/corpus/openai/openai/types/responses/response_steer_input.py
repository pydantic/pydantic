# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .response_steer_input_content import ResponseSteerInputContent
from .response_function_call_output_item_list import ResponseFunctionCallOutputItemList

class ResponseSteerInputItemListMessage(BaseModel):
    content: Union[List[ResponseSteerInputContent], str]
    role: Literal['user']
    type: Literal['message']
    id: Optional[str] = None
    status: Optional[str] = None

class ResponseSteerInputItemListFunctionCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class ResponseSteerInputItemListFunctionCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ResponseSteerInputItemListFunctionCallOutputCaller: TypeAlias = Annotated[Union[ResponseSteerInputItemListFunctionCallOutputCallerDirect, ResponseSteerInputItemListFunctionCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseSteerInputItemListFunctionCallOutput(BaseModel):
    """The output of a function tool call."""
    output: Union[str, ResponseFunctionCallOutputItemList]
    type: Literal['function_call_output']
    id: Optional[str] = None
    call_id: Optional[str] = None
    caller: Optional[ResponseSteerInputItemListFunctionCallOutputCaller] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
ResponseSteerInputItemList: TypeAlias = Annotated[Union[ResponseSteerInputItemListMessage, ResponseSteerInputItemListFunctionCallOutput], PropertyInfo(discriminator='type')]
ResponseSteerInput: TypeAlias = Union[str, List[ResponseSteerInputItemList]]
