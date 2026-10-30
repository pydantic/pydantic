# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .decision_input_text import DecisionInputText
from .decision_user_message import DecisionUserMessage
from .decision_system_message import DecisionSystemMessage
from .decision_assistant_message import DecisionAssistantMessage
from .decision_developer_message import DecisionDeveloperMessage

class ItemFunctionCall(BaseModel):
    arguments: str
    call_id: str
    name: str
    type: Literal['function_call']
    id: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemFunctionCallOutputOutputPartsInputImage(BaseModel):
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None
ItemFunctionCallOutputOutputParts: TypeAlias = Annotated[Union[DecisionInputText, ItemFunctionCallOutputOutputPartsInputImage], PropertyInfo(discriminator='type')]

class ItemFunctionCallOutput(BaseModel):
    call_id: str
    output: Union[str, List[ItemFunctionCallOutputOutputParts]]
    type: Literal['function_call_output']
    id: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemCustomToolCall(BaseModel):
    call_id: str
    input: str
    name: str
    type: Literal['custom_tool_call']
    id: Optional[str] = None
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemCustomToolCallOutputOutputPartsInputImage(BaseModel):
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None
ItemCustomToolCallOutputOutputParts: TypeAlias = Annotated[Union[DecisionInputText, ItemCustomToolCallOutputOutputPartsInputImage], PropertyInfo(discriminator='type')]

class ItemCustomToolCallOutput(BaseModel):
    call_id: str
    output: Union[str, List[ItemCustomToolCallOutputOutputParts]]
    type: Literal['custom_tool_call_output']
    id: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
ItemUnion: TypeAlias = Annotated[Union[DecisionUserMessage, DecisionDeveloperMessage, DecisionSystemMessage, DecisionAssistantMessage, ItemFunctionCall, ItemFunctionCallOutput, ItemCustomToolCall, ItemCustomToolCallOutput], PropertyInfo(discriminator='type')]

class DecisionItemCreateEvent(BaseModel):
    """
    Append an input item for future decisions without starting an evaluation or changing Live voice context.
    """
    item: ItemUnion
    type: Literal['decision.item.create']
    event_id: Optional[str] = None
