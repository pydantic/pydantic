# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel
from .chatkit_widget_item import ChatKitWidgetItem
from .chatkit_thread_user_message_item import ChatKitThreadUserMessageItem
from .chatkit_thread_assistant_message_item import ChatKitThreadAssistantMessageItem

class DataChatKitClientToolCall(BaseModel):
    """Record of a client side tool invocation initiated by the assistant."""
    id: str
    arguments: str
    call_id: str
    created_at: int
    name: str
    object: Literal['chatkit.thread_item']
    output: Optional[str] = None
    status: Literal['in_progress', 'completed']
    thread_id: str
    type: Literal['chatkit.client_tool_call']

class DataChatKitTask(BaseModel):
    """Task emitted by the workflow to show progress and status updates."""
    id: str
    created_at: int
    heading: Optional[str] = None
    object: Literal['chatkit.thread_item']
    summary: Optional[str] = None
    task_type: Literal['custom', 'thought']
    thread_id: str
    type: Literal['chatkit.task']

class DataChatKitTaskGroupTask(BaseModel):
    """Task entry that appears within a TaskGroup."""
    heading: Optional[str] = None
    summary: Optional[str] = None
    type: Literal['custom', 'thought']

class DataChatKitTaskGroup(BaseModel):
    """Collection of workflow tasks grouped together in the thread."""
    id: str
    created_at: int
    object: Literal['chatkit.thread_item']
    tasks: List[DataChatKitTaskGroupTask]
    thread_id: str
    type: Literal['chatkit.task_group']
Data: TypeAlias = Annotated[Union[ChatKitThreadUserMessageItem, ChatKitThreadAssistantMessageItem, ChatKitWidgetItem, DataChatKitClientToolCall, DataChatKitTask, DataChatKitTaskGroup], PropertyInfo(discriminator='type')]

class ChatKitThreadItemList(BaseModel):
    """A paginated list of thread items rendered for the ChatKit API."""
    data: List[Data]
    first_id: Optional[str] = None
    has_more: bool
    last_id: Optional[str] = None
    object: Literal['list']
