
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSpendLimitScopedAPIKeyActor(BaseModel):
    """A scoped Admin API key acting on behalf of the organization."""
    scoped_api_key_id: str
    type: Literal['scoped_api_key_actor']
