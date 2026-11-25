
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaManagedAgentsInjectionLocationResponse(BaseModel):
    """Where in the outbound request the secret value is substituted."""
    body: bool
    header: bool
