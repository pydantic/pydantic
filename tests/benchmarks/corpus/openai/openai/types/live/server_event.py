# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class SessionInputAudioAppend(BaseModel):
    """
    Input audio received from the primary transport and reflected to a Live sideband connection before model-input muting.
    """
    audio: str
    type: Literal['session.input_audio.append']

class TransportDtmfReceived(BaseModel):
    """A SIP DTMF keypress received from the caller.

    Delivered only to sideband observers.
    """
    event: str
    event_id: str
    type: Literal['transport.dtmf.received']

class TransportDtmfSend(BaseModel):
    """A SIP DTMF keypress successfully sent to the SIP trunk.

    Delivered only to sideband observers; this is not a client command.
    """
    event: str
    event_id: str
    type: Literal['transport.dtmf.send']
    client_event_id: Optional[str] = None

class TransportRinging(BaseModel):
    """The outbound SIP provider leg is ringing or providing early media.

    Delivered only to sideband observers.
    """
    event_id: str
    session_id: str
    type: Literal['transport.ringing']

class TransportAnswered(BaseModel):
    """The outbound SIP provider leg answered and media is established.

    Delivered only to sideband observers.
    """
    event_id: str
    session_id: str
    type: Literal['transport.answered']

class TransportFailedError(BaseModel):
    code: str
    message: str
    type: Literal['call_error']
    param: Optional[str] = None

class TransportFailed(BaseModel):
    """An asynchronous outbound SIP setup failure.

    Delivered only to sideband observers.
    """
    error: TransportFailedError
    event_id: str
    session_id: str
    type: Literal['transport.failed']
