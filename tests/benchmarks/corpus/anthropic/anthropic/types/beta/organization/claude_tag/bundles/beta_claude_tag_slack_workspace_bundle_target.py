
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ......_models import BaseModel

class BetaClaudeTagSlackWorkspaceBundleTarget(BaseModel):
    """One Bundle attached to one Slack workspace.

    The Bundle can be used in the workspace and in every channel in it.
    """
    id: str
    created_at: datetime
    slack_workspace_id: str
    type: Literal['slack_workspace']
