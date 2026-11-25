
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaPluginUserActor(BaseModel):
    email_address: Optional[str] = None
    type: Literal['user_actor']
    user_id: str
