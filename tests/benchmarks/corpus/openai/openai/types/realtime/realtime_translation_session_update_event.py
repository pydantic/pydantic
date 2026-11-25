# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_translation_session_update_request import RealtimeTranslationSessionUpdateRequest

class RealtimeTranslationSessionUpdateEvent(BaseModel):
    """Send this event to update the translation session configuration.

    Translation
    sessions support updates to `audio.output.language`, `audio.input.transcription`,
    and `audio.input.noise_reduction`.
    """
    session: RealtimeTranslationSessionUpdateRequest
    type: Literal['session.update']
    event_id: Optional[str] = None
