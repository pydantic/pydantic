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
    call_id: str
    sip_headers: List[DataSipHeader]
    sip_media_security: Union[Literal['rtp', 'srtp'], str, None] = None

class RealtimeCallIncomingWebhookEvent(BaseModel):
    """
    Sent when an incoming API SIP session is available for Realtime acceptance.
    The same pending session can also emit `live.transport.incoming`; the first
    successful Realtime or Live accept endpoint selects the runtime surface.
    """
    id: str
    created_at: int
    data: Data
    type: Literal['realtime.call.incoming']
    object: Optional[Literal['event']] = None
