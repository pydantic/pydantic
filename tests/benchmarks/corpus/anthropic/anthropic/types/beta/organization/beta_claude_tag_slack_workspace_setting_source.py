
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagSlackWorkspaceSettingSource(BaseModel):
    """The value comes from a Slack workspace of the organization."""
    slack_workspace_id: str
    type: Literal['slack_workspace']
