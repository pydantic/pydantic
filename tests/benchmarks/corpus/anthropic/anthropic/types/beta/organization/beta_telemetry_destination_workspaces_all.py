
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaTelemetryDestinationWorkspacesAll(BaseModel):
    """
    The destination covers every workspace of the organization, including the default workspace, archived workspaces, and workspaces created later. It doesn't have a list.
    """
    type: Literal['all']
