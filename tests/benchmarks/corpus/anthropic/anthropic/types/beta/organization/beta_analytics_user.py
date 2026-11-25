
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaAnalyticsUser(BaseModel):
    """A user in the organization, identified by tagged id and email address."""
    id: str
    email_address: str
    type: Literal['user']
