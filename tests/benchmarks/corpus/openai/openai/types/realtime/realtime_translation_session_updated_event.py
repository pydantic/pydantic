# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .realtime_translation_session import RealtimeTranslationSession

class RealtimeTranslationSessionUpdatedEvent(BaseModel):
    """
    Returned when a translation session is updated with a `session.update` event,
    unless there is an error.
    """
    event_id: str
    session: RealtimeTranslationSession
    type: Literal['session.updated']
