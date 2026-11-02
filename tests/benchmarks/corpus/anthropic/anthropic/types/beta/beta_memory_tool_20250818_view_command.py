
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaMemoryTool20250818ViewCommand(BaseModel):
    command: Literal['view']
    path: str
    view_range: Optional[List[int]] = None
