
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagSlackParentChannelSettingSource(BaseModel):
    """The value comes from the channel that a code channel was started from.

    A parent channel contributes `instructions` and `environment_id` only.
    """
    slack_channel_id: str
    type: Literal['slack_parent_channel']
