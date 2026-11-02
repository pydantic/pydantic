
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsServiceAccountExecutionIdentity(BaseModel):
    """The Anthropic-managed service account as returned in API responses."""
    type: Literal['service_account']
