
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationWorkspacesInclude(BaseModel):
    """The destination covers the workspaces on its list, and no others."""
    type: Literal['include']
