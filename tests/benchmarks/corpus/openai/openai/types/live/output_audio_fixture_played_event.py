# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class OutputAudioFixturePlayedEvent(BaseModel):
    """
    The complete audio fixture has drained from the server mixer and normal inference has resumed. Transport buffers may still contain audio; this event does not prove listener-side completion. The optional client_event_id echoes the play command. This event is not emitted for canceled or failed playback.
    """
    event_id: str
    type: Literal['session.output_audio.fixture.played']
    client_event_id: Optional[str] = None
