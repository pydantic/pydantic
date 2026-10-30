# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class DataSipHeader(BaseModel):
    """A header from the SIP Invite."""
    name: str
    value: str

class Data(BaseModel):
    """Event data payload."""
    session_id: str
    sip_headers: List[DataSipHeader]
    type: Literal['sip']
    sip_media_security: Union[Literal['rtp', 'srtp'], str, None] = None

class LiveTransportIncomingWebhookEvent(BaseModel):
    """Sent when an incoming API SIP session is available for Live acceptance.

    The
    same pending session can also emit `realtime.call.incoming`; the first
    successful Realtime or Live accept endpoint selects the runtime surface.
    """
    id: str
    created_at: int
    data: Data
    type: Literal['live.transport.incoming']
    object: Optional[Literal['event']] = None
