
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ......_models import BaseModel

class BetaClaudeTagSlackChannelBundleTarget(BaseModel):
    """One Bundle attached to one Slack channel.

    The Bundle can be used in that channel only.
    """
    id: str
    created_at: datetime
    slack_channel_id: str
    type: Literal['slack_channel']
