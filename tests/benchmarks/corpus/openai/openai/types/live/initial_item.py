# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class DeveloperContent(BaseModel):
    """Text supplied in a developer or user message when starting a Live session."""
    text: str
    type: Optional[Literal['input_text']] = None

class Developer(BaseModel):
    """A developer message included in the initial text history of a Live session."""
    content: List[DeveloperContent]
    role: Literal['developer']
    id: Optional[str] = None
    status: Optional[Literal['incomplete', 'completed']] = None
    type: Optional[Literal['message']] = None

class UserContent(BaseModel):
    """Text supplied in a developer or user message when starting a Live session."""
    text: str
    type: Optional[Literal['input_text']] = None

class User(BaseModel):
    """A user message included in the initial text history of a Live session."""
    content: List[UserContent]
    role: Literal['user']
    id: Optional[str] = None
    status: Optional[Literal['incomplete', 'completed']] = None
    type: Optional[Literal['message']] = None

class AssistantContentText(BaseModel):
    """Assistant text supplied as conversation history when starting a Live session."""
    text: str
    type: Optional[Literal['text']] = None

class AssistantContentOutputText(BaseModel):
    """
    Assistant output text supplied as conversation history when starting a Live session.
    """
    text: str
    type: Literal['output_text']
AssistantContent: TypeAlias = Annotated[Union[AssistantContentText, AssistantContentOutputText], PropertyInfo(discriminator='type')]

class Assistant(BaseModel):
    """An assistant message included in the initial text history of a Live session."""
    content: List[AssistantContent]
    role: Literal['assistant']
    id: Optional[str] = None
    status: Optional[Literal['incomplete', 'completed']] = None
    type: Optional[Literal['message']] = None
InitialItem: TypeAlias = Annotated[Union[Developer, User, Assistant], PropertyInfo(discriminator='role')]
