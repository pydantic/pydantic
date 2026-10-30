
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class InputAudioBufferClearEvent(BaseModel):
    type: Literal['input_audio_buffer.clear']
    event_id: Optional[str] = None
