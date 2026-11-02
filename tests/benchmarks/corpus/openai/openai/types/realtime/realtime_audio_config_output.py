# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .realtime_audio_formats import RealtimeAudioFormats

class VoiceID(BaseModel):
    """Custom voice reference."""
    id: str
Voice: TypeAlias = Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'], VoiceID]

class RealtimeAudioConfigOutput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    speed: Optional[float] = None
    voice: Optional[Voice] = None
