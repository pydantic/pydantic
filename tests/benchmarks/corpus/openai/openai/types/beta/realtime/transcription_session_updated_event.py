
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .transcription_session import TranscriptionSession

class TranscriptionSessionUpdatedEvent(BaseModel):
    event_id: str
    session: TranscriptionSession
    type: Literal['transcription_session.updated']
