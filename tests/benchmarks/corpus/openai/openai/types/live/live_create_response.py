# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class Session(BaseModel):
    """The newly created Live session.

    Use its ID for session controls and sideband connections.
    """
    id: str

class Transport(BaseModel):
    """WebRTC transport with the SDP answer."""
    sdp: str
    type: Literal['webrtc']

class LiveCreateResponse(BaseModel):
    """The created Live session identifier and WebRTC answer.

    Apply transport.sdp as the peer's remote answer and wait for session.started on the data channel before sending commands.
    """
    session: Session
    transport: Transport
