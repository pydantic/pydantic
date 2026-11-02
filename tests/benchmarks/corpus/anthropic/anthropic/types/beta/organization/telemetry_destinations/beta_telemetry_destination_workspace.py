
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel

class BetaTelemetryDestinationWorkspace(BaseModel):
    """A workspace on a telemetry destination's workspace list.

    Under `include`, the destination covers the workspace. Under `exclude`, the destination covers every workspace except this one. The entry doesn't have an `id`. Its `telemetry_destination_id` and `workspace_id` together identify it.
    """
    created_at: datetime
    telemetry_destination_id: str
    type: Literal['telemetry_destination_workspace']
    workspace_id: str
