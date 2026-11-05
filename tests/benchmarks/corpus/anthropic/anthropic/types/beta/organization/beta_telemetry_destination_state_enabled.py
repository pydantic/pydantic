
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationStateEnabled(BaseModel):
    """The telemetry destination receives the spans of the workspaces that it covers."""
    type: Literal['enabled']
