
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaUserProfileActionURL(BaseModel):
    """A URL to give to the person who takes the requested action."""
    expires_at: datetime
    type: Literal['user_profile_action_url']
    url: str
