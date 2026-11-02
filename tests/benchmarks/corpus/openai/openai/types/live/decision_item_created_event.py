# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .decision_input_text import DecisionInputText
from .decision_stored_user_message import DecisionStoredUserMessage
from .decision_stored_system_message import DecisionStoredSystemMessage
from .decision_stored_assistant_message import DecisionStoredAssistantMessage
from .decision_stored_developer_message import DecisionStoredDeveloperMessage

class ItemFunctionCall(BaseModel):
    id: str
    arguments: str
    call_id: str
    name: str
    type: Literal['function_call']
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemFunctionCallOutputOutputPartsInputImage(BaseModel):
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None
ItemFunctionCallOutputOutputParts: TypeAlias = Annotated[Union[DecisionInputText, ItemFunctionCallOutputOutputPartsInputImage], PropertyInfo(discriminator='type')]

class ItemFunctionCallOutput(BaseModel):
    id: str
    call_id: str
    output: Union[str, List[ItemFunctionCallOutputOutputParts]]
    type: Literal['function_call_output']
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemCustomToolCall(BaseModel):
    id: str
    call_id: str
    input: str
    name: str
    type: Literal['custom_tool_call']
    namespace: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None

class ItemCustomToolCallOutputOutputPartsInputImage(BaseModel):
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None
ItemCustomToolCallOutputOutputParts: TypeAlias = Annotated[Union[DecisionInputText, ItemCustomToolCallOutputOutputPartsInputImage], PropertyInfo(discriminator='type')]

class ItemCustomToolCallOutput(BaseModel):
    id: str
    call_id: str
    output: Union[str, List[ItemCustomToolCallOutputOutputParts]]
    type: Literal['custom_tool_call_output']
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
ItemUnion: TypeAlias = Annotated[Union[DecisionStoredUserMessage, DecisionStoredDeveloperMessage, DecisionStoredSystemMessage, DecisionStoredAssistantMessage, ItemFunctionCall, ItemFunctionCallOutput, ItemCustomToolCall, ItemCustomToolCallOutput], PropertyInfo(discriminator='type')]

class DecisionItemCreatedEvent(BaseModel):
    """An input item was appended for future decisions."""
    event_id: str
    item: ItemUnion
    type: Literal['decision.item.created']
    client_event_id: Optional[str] = None
