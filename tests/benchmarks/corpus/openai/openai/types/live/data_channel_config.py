# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal
from ..._models import BaseModel
from .server_event_selector import ServerEventSelector

class DataChannelConfig(BaseModel):
    """
    Control which Live events an untrusted WebRTC frontend can send and receive over its data channel. These restrictions do not apply to trusted sideband connections.
    """
    allowed_client_events: Union[Literal['all'], List[str], None] = None
    allowed_server_events: Union[Literal['all'], List[ServerEventSelector], None] = None
