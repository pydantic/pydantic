
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationTestFailure(BaseModel):
    """The test span was not delivered."""
    error: str
    type: Literal['failure']
