
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaServerToolCaller20260120(BaseModel):
    tool_id: str
    type: Literal['code_execution_20260120']
