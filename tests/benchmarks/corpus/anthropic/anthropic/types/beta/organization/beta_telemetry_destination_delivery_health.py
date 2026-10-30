
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from ...._models import BaseModel

class BetaTelemetryDestinationDeliveryHealth(BaseModel):
    """
    The most recent delivery results that the API records for a telemetry destination.

    Changes to the destination's configuration or state don't reset these fields. Changes to these fields don't change `updated_at`. The values can lag behind the latest deliveries.

    See the [OpenTelemetry export guide](https://platform.claude.com/docs/en/manage-claude/opentelemetry#delivery-and-health) to learn how the API delivers spans and when it disables a destination.
    """
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
