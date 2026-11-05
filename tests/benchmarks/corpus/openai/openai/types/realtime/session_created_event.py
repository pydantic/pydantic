# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .realtime_session_create_request import RealtimeSessionCreateRequest
from .realtime_transcription_session_create_request import RealtimeTranscriptionSessionCreateRequest
Session: TypeAlias = Union[RealtimeSessionCreateRequest, RealtimeTranscriptionSessionCreateRequest]

class SessionCreatedEvent(BaseModel):
    """Returned when a Session is created.

    Emitted automatically when a new
    connection is established as the first server event. This event will contain
    the default Session configuration.
    """
    event_id: str
    session: Session
    type: Literal['session.created']
