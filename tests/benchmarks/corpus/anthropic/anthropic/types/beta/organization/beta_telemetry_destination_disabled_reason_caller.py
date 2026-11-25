
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationDisabledReasonCaller(BaseModel):
    """
    A caller disabled the destination with an update that set `state` to `disabled`.
    """
    type: Literal['caller']
