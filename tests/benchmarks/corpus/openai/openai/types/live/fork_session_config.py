# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .audio_format import AudioFormat
from .client_config import ClientConfig
from .responses_delegation_update_config import ResponsesDelegationUpdateConfig

class Audio(BaseModel):
    """Audio format for a WebSocket fork.

    WebRTC forks negotiate their audio format and must omit this field.
    """
    format: Optional[AudioFormat] = None

class Delegation(BaseModel):
    """Overrides for the stored session’s Responses backend.

    Only supported when the stored session already uses Responses delegation; the delegation type cannot change.
    """
    type: Literal['responses']
    acknowledgement_delay_ms: Optional[int] = None
    responses: Optional[ResponsesDelegationUpdateConfig] = None

class ForkSessionConfig(BaseModel):
    """Overrides for a stored session after connecting to the fork WebSocket.

    An empty object inherits the stored configuration; do not supply a new model. audio.format applies only to the new WebSocket connection. client overrides are only supported for WebRTC forks.
    """
    audio: Optional[Audio] = None
    client: Optional[ClientConfig] = None
    delegation: Optional[Delegation] = None
    store: Optional[bool] = None
