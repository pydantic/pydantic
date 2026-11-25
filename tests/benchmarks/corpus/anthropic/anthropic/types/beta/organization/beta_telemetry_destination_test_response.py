
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_telemetry_destination_test_result import BetaTelemetryDestinationTestResult

class BetaTelemetryDestinationTestResponse(BaseModel):
    """The result of one test span sent to a destination."""
    result: BetaTelemetryDestinationTestResult
    type: Literal['telemetry_destination_test']
