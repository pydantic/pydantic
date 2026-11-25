# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .realtime_audio_formats import RealtimeAudioFormats

class OutputVoiceID(BaseModel):
    """Custom voice reference."""
    id: str
OutputVoice: TypeAlias = Union[str, Literal['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'], OutputVoiceID]

class Output(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    voice: Optional[OutputVoice] = None

class RealtimeResponseCreateAudioOutput(BaseModel):
    """Configuration for audio input and output."""
    output: Optional[Output] = None
