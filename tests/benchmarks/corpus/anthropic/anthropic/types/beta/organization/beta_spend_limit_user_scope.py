
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSpendLimitUserScope(BaseModel):
    """Scope selecting a single member of the organization."""
    type: Literal['user']
    user_id: str
