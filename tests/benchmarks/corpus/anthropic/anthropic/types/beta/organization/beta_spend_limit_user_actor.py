
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSpendLimitUserActor(BaseModel):
    """A user within the organization.

    `name` and `email_address` are
    null when the underlying account is unavailable or has been deleted;
    `deleted` is true only for deleted accounts.
    """
    deleted: bool
    email_address: Optional[str] = None
    name: Optional[str] = None
    type: Literal['user_actor']
    user_id: str
