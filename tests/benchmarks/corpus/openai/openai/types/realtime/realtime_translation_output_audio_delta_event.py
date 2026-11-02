# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class RealtimeTranslationOutputAudioDeltaEvent(BaseModel):
    """Returned when translated output audio is available.

    The `delta` contains a
    PCM16 audio chunk whose length can vary. Clients should decode and queue the
    complete delta instead of assuming a fixed byte or sample count.
    """
    delta: str
    event_id: str
    type: Literal['session.output_audio.delta']
    channels: Optional[int] = None
    elapsed_ms: Optional[int] = None
    format: Optional[Literal['pcm16']] = None
    sample_rate: Optional[int] = None
