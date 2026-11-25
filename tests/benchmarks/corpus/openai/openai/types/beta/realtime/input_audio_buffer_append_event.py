
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class InputAudioBufferAppendEvent(BaseModel):
    audio: str
    type: Literal['input_audio_buffer.append']
    event_id: Optional[str] = None
