# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_response_steer_input_content import BetaResponseSteerInputContent
from .beta_response_function_call_output_item_list import BetaResponseFunctionCallOutputItemList

class ResponseSteerInputItemListMessageAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ResponseSteerInputItemListMessage(BaseModel):
    content: Union[List[BetaResponseSteerInputContent], str]
    role: Literal['user']
    type: Literal['message']
    id: Optional[str] = None
    agent: Optional[ResponseSteerInputItemListMessageAgent] = None
    status: Optional[str] = None

class ResponseSteerInputItemListFunctionCallOutputAgent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class ResponseSteerInputItemListFunctionCallOutputCallerDirect(BaseModel):
    type: Literal['direct']

class ResponseSteerInputItemListFunctionCallOutputCallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
ResponseSteerInputItemListFunctionCallOutputCaller: TypeAlias = Annotated[Union[ResponseSteerInputItemListFunctionCallOutputCallerDirect, ResponseSteerInputItemListFunctionCallOutputCallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseSteerInputItemListFunctionCallOutput(BaseModel):
    """The output of a function tool call."""
    output: Union[str, BetaResponseFunctionCallOutputItemList]
    type: Literal['function_call_output']
    id: Optional[str] = None
    agent: Optional[ResponseSteerInputItemListFunctionCallOutputAgent] = None
    call_id: Optional[str] = None
    caller: Optional[ResponseSteerInputItemListFunctionCallOutputCaller] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
ResponseSteerInputItemList: TypeAlias = Annotated[Union[ResponseSteerInputItemListMessage, ResponseSteerInputItemListFunctionCallOutput], PropertyInfo(discriminator='type')]
BetaResponseSteerInput: TypeAlias = Union[str, List[ResponseSteerInputItemList]]
