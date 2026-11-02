
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_telemetry_destination_disabled_reason import BetaTelemetryDestinationDisabledReason

class BetaTelemetryDestinationStateDisabled(BaseModel):
    """The API doesn't deliver anything to the telemetry destination.

    Spans produced while it is disabled aren't delivered later.
    """
    reason: BetaTelemetryDestinationDisabledReason
    type: Literal['disabled']
