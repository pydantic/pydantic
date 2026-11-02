
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class BetaDeletedTelemetryDestinationWorkspace(BaseModel):
    """Confirmation that a workspace was removed from a destination's list."""
    telemetry_destination_id: str
    type: Literal['telemetry_destination_workspace_deleted']
    workspace_id: str
