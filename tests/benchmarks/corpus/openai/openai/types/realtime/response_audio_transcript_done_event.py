# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseAudioTranscriptDoneEvent(BaseModel):
    """
    Returned when the model-generated transcription of audio output is done
    streaming. Also emitted when a Response is interrupted, incomplete, or
    cancelled.
    """
    content_index: int
    event_id: str
    item_id: str
    output_index: int
    response_id: str
    transcript: str
    type: Literal['response.output_audio_transcript.done']
