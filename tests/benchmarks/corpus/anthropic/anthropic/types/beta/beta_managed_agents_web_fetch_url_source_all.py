
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsWebFetchURLSourceAll(BaseModel):
    """Every URL from this source may be fetched. This is the default."""
    type: Literal['all']
