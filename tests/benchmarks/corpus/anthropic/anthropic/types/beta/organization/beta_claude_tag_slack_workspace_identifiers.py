
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaClaudeTagSlackWorkspaceIdentifiers(BaseModel):
    """The identifier Slack shows for a workspace.

    It is Slack's own, not an identifier of this API.
    """
    workspace_id: str
