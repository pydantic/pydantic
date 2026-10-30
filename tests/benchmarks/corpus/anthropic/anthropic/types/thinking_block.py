
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class ThinkingBlock(BaseModel):
    signature: str
    thinking: str
    type: Literal['thinking']
