
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaClaudeTagSlackDefaultSettingSource(BaseModel):
    """
    The value comes from the organization's Slack defaults, which have no identifier.
    """
    type: Literal['slack_default']
