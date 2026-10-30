
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaToolReferenceBlock(BaseModel):
    tool_name: str
    type: Literal['tool_reference']
