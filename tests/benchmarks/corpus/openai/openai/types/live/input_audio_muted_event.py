# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioMutedEvent(BaseModel):
    """Acknowledges a session.input_audio.mute command.

    An independent input mute sends silence to the model and preserves sideband audio reflection. Fixture playback does not emit this event.
    """
    event_id: str
    type: Literal['session.input_audio.muted']
    client_event_id: Optional[str] = None
