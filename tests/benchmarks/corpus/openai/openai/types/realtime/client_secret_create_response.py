# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .realtime_session_create_response import RealtimeSessionCreateResponse
from .realtime_transcription_session_create_response import RealtimeTranscriptionSessionCreateResponse
Session: TypeAlias = Annotated[Union[RealtimeSessionCreateResponse, RealtimeTranscriptionSessionCreateResponse], PropertyInfo(discriminator='type')]

class ClientSecretCreateResponse(BaseModel):
    """Response from creating a session and client secret for the Realtime API."""
    expires_at: int
    session: Session
    value: str
