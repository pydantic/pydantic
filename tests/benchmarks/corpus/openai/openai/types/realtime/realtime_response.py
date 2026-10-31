# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.metadata import Metadata
from .conversation_item import ConversationItem
from .realtime_audio_formats import RealtimeAudioFormats
from .realtime_response_usage import RealtimeResponseUsage
from .realtime_response_status import RealtimeResponseStatus

class AudioOutput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    voice: Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'], None] = None

class Audio(BaseModel):
    """Configuration for audio output."""
    output: Optional[AudioOutput] = None

class RealtimeResponse(BaseModel):
    """The response resource."""
    id: Optional[str] = None
    audio: Optional[Audio] = None
    conversation_id: Optional[str] = None
    max_output_tokens: Union[int, Literal['inf'], None] = None
    metadata: Optional[Metadata] = None
    object: Optional[Literal['realtime.response']] = None
    output: Optional[List[ConversationItem]] = None
    output_modalities: Optional[List[Literal['text', 'audio']]] = None
    status: Optional[Literal['completed', 'cancelled', 'failed', 'incomplete', 'in_progress']] = None
    status_details: Optional[RealtimeResponseStatus] = None
    usage: Optional[RealtimeResponseUsage] = None
