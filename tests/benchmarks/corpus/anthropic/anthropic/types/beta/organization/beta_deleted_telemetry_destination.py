
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaDeletedTelemetryDestination(BaseModel):
    """Confirmation that a destination was deleted."""
    id: str
    type: Literal['telemetry_destination_deleted']
