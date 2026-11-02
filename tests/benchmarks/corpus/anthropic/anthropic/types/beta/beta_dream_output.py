
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaDreamOutput(BaseModel):
    """
    An entry in a dream's `outputs` that references the memory store holding its result.
    """
    memory_store_id: str
    type: Literal['memory_store']
