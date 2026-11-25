
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsRedactedBlock(BaseModel):
    """Placeholder for content withheld by Anthropic model policy."""
    type: Literal['redacted']
