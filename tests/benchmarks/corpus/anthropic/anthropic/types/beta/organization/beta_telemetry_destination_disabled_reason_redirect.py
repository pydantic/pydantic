
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationDisabledReasonRedirect(BaseModel):
    """
    The API disabled the destination because the endpoint answered a delivery with a 3xx status. Redirects are never followed, and one such answer disables the destination at once.
    """
    type: Literal['redirect']
