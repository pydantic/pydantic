
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSessionWorkData(BaseModel):
    """Work data for session work items.

    This resource type is used when work represents a session that needs to be executed
    in a self-hosted environment.
    """
    id: str
    type: Literal['session']
