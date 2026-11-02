
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAPIActor(BaseModel):
    """
    A direct caller of the public API, identified by the API key that authenticated the request.
    """
    api_key_id: str
    type: Literal['api_actor']
