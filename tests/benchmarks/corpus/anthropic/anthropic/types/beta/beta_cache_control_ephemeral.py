
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaCacheControlEphemeral(BaseModel):
    type: Literal['ephemeral']
    ttl: Optional[Literal['5m', '1h']] = None
