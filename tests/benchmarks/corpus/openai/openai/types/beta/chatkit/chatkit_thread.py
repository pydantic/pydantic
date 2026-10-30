# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel

class StatusActive(BaseModel):
    """Indicates that a thread is active."""
    type: Literal['active']

class StatusLocked(BaseModel):
    """Indicates that a thread is locked and cannot accept new input."""
    reason: Optional[str] = None
    type: Literal['locked']

class StatusClosed(BaseModel):
    """Indicates that a thread has been closed."""
    reason: Optional[str] = None
    type: Literal['closed']
Status: TypeAlias = Annotated[Union[StatusActive, StatusLocked, StatusClosed], PropertyInfo(discriminator='type')]

class ChatKitThread(BaseModel):
    """Represents a ChatKit thread and its current status."""
    id: str
    created_at: int
    object: Literal['chatkit.thread']
    status: Status
    title: Optional[str] = None
    user: str
