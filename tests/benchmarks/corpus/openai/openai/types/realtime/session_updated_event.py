# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .realtime_session_create_request import RealtimeSessionCreateRequest
from .realtime_transcription_session_create_request import RealtimeTranscriptionSessionCreateRequest
Session: TypeAlias = Union[RealtimeSessionCreateRequest, RealtimeTranscriptionSessionCreateRequest]

class SessionUpdatedEvent(BaseModel):
    """
    Returned when a session is updated with a `session.update` event, unless
    there is an error.
    """
    event_id: str
    session: Session
    type: Literal['session.updated']
