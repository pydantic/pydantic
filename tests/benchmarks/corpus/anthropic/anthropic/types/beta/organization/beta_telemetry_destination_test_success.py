
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationTestSuccess(BaseModel):
    """The destination answered the test span with a 2xx status."""
    type: Literal['success']
