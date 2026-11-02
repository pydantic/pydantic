
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from ...shared.metadata import Metadata
from .conversation_item import ConversationItem
from .realtime_response_usage import RealtimeResponseUsage
from .realtime_response_status import RealtimeResponseStatus

class RealtimeResponse(BaseModel):
    id: Optional[str] = None
    conversation_id: Optional[str] = None
    max_output_tokens: Union[int, Literal['inf'], None] = None
    metadata: Optional[Metadata] = None
    modalities: Optional[List[Literal['text', 'audio']]] = None
    object: Optional[Literal['realtime.response']] = None
    output: Optional[List[ConversationItem]] = None
    output_audio_format: Optional[Literal['pcm16', 'g711_ulaw', 'g711_alaw']] = None
    status: Optional[Literal['completed', 'cancelled', 'failed', 'incomplete', 'in_progress']] = None
    status_details: Optional[RealtimeResponseStatus] = None
    temperature: Optional[float] = None
    usage: Optional[RealtimeResponseUsage] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse'], None] = None
