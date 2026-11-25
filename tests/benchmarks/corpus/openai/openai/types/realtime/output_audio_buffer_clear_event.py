# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class OutputAudioBufferClearEvent(BaseModel):
    """**WebRTC/SIP Only:** Emit to cut off the current audio response.

    This will trigger the server to
    stop generating audio and emit a `output_audio_buffer.cleared` event. This
    event should be preceded by a `response.cancel` client event to stop the
    generation of the current response.
    [Learn more](https://developers.openai.com/api/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc).
    """
    type: Literal['output_audio_buffer.clear']
    event_id: Optional[str] = None
