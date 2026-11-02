# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioUnmutedEvent(BaseModel):
    """
    Acknowledges a session.input_audio.unmute command, removing the independent input mute. An active audio fixture still pauses inference until playback finishes. Fixture playback does not emit this event.
    """
    event_id: str
    type: Literal['session.input_audio.unmuted']
    client_event_id: Optional[str] = None
