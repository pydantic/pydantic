# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel
from .data_channel_config import DataChannelConfig

class ClientConfig(BaseModel):
    """
    Startup-only capabilities for an untrusted frontend attached to a unified WebRTC session. Trusted sideband connections are unaffected.
    """
    data_channel: DataChannelConfig
