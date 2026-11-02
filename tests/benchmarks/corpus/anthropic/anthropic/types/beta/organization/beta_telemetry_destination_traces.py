
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_telemetry_destination_content_mode import BetaTelemetryDestinationContentMode

class BetaTelemetryDestinationTraces(BaseModel):
    """A telemetry destination's settings for the traces it receives."""
    content_mode: BetaTelemetryDestinationContentMode
    enabled: bool
    endpoint_url: Optional[str] = None
    max_content_bytes: Optional[int] = None
