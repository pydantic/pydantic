
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaToolBash20241022(BaseModel):
    name: Literal['bash']
    type: Literal['bash_20241022']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    defer_loading: Optional[bool] = None
    input_examples: Optional[List[Dict[str, object]]] = None
    strict: Optional[bool] = None
