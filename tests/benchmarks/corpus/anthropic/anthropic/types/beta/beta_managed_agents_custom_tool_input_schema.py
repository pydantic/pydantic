
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsCustomToolInputSchema(BaseModel):
    """JSON Schema for custom tool input parameters."""
    type: Literal['object']
    properties: Optional[Dict[str, object]] = None
    required: Optional[List[str]] = None
    __pydantic_extra__: Dict[str, object]
