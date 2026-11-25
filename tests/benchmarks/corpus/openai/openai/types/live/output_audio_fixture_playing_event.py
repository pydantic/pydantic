# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class OutputAudioFixturePlayingEvent(BaseModel):
    """The existing playback path has accepted the validated audio fixture.

    This acknowledgment does not identify when the listener receives the first sample. The optional client_event_id echoes the play command.
    """
    event_id: str
    type: Literal['session.output_audio.fixture.playing']
    client_event_id: Optional[str] = None
