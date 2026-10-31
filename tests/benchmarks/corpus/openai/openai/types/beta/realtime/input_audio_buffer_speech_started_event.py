
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class InputAudioBufferSpeechStartedEvent(BaseModel):
    audio_start_ms: int
    event_id: str
    item_id: str
    type: Literal['input_audio_buffer.speech_started']
