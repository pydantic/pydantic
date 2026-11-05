
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_telemetry_destination_state import BetaTelemetryDestinationState
from .beta_telemetry_destination_traces import BetaTelemetryDestinationTraces
from .beta_telemetry_destination_workspaces import BetaTelemetryDestinationWorkspaces
from .beta_telemetry_destination_delivery_health import BetaTelemetryDestinationDeliveryHealth

class BetaTelemetryDestination(BaseModel):
    """
    An OpenTelemetry destination: an OTLP/HTTP endpoint, the request headers sent with every delivery to it, what the exported spans contain, and which workspaces it covers. A destination belongs to an organization. A workspace's spans go to every enabled destination that covers it.
    """
    id: str
    created_at: datetime
    delivery_health: BetaTelemetryDestinationDeliveryHealth
    display_name: Optional[str] = None
    endpoint_url: str
    header_names: List[str]
    state: BetaTelemetryDestinationState
    traces: BetaTelemetryDestinationTraces
    type: Literal['telemetry_destination']
    updated_at: datetime
    workspaces: BetaTelemetryDestinationWorkspaces
