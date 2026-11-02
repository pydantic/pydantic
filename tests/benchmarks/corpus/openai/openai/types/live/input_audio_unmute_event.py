# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioUnmuteEvent(BaseModel):
    """Resume audio input to a Live model after muting it.

    The server acknowledges with `session.input_audio.unmuted`. An active audio fixture still pauses inference until playback finishes.
    """
    type: Literal['session.input_audio.unmute']
    event_id: Optional[str] = None
