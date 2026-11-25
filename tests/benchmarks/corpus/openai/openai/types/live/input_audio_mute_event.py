# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InputAudioMuteEvent(BaseModel):
    """Mute audio input to the Live model without closing the session.

    The server acknowledges with `session.input_audio.muted`.
    """
    type: Literal['session.input_audio.mute']
    event_id: Optional[str] = None
