
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from ...shared.metadata import Metadata
from .conversation_item_with_reference import ConversationItemWithReference

class ResponseTool(BaseModel):
    description: Optional[str] = None
    name: Optional[str] = None
    parameters: Optional[object] = None
    type: Optional[Literal['function']] = None

class Response(BaseModel):
    conversation: Union[str, Literal['auto', 'none'], None] = None
    input: Optional[List[ConversationItemWithReference]] = None
    instructions: Optional[str] = None
    max_response_output_tokens: Union[int, Literal['inf'], None] = None
    metadata: Optional[Metadata] = None
    modalities: Optional[List[Literal['text', 'audio']]] = None
    output_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    temperature: Optional[float] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[ResponseTool]] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse'], None] = None

class ResponseCreateEvent(BaseModel):
    type: Literal['response.create']
    event_id: Optional[str] = None
    response: Optional[Response] = None
