
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_tool_input_schema import BetaResponseToolInputSchema

class BetaResponseTool(BaseModel):
    """A custom tool definition, as sent."""
    input_schema: BetaResponseToolInputSchema
    name: str
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    defer_loading: Optional[bool] = None
    description: Optional[str] = None
    eager_input_streaming: Optional[bool] = None
    input_examples: Optional[List[Dict[str, object]]] = None
    strict: Optional[bool] = None
    type: Optional[Literal['custom']] = None
