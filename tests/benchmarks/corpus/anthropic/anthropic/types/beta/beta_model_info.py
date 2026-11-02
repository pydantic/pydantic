
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_model_line import BetaModelLine
from .beta_model_capabilities import BetaModelCapabilities

class BetaModelInfo(BaseModel):
    id: str
    allowed_fallback_models: Optional[List[str]] = None
    capabilities: Optional[BetaModelCapabilities] = None
    created_at: datetime
    deprecated_at: Optional[datetime] = None
    display_name: str
    lifecycle: Literal['active', 'deprecated', 'retired']
    line: Optional[BetaModelLine] = None
    max_input_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    retires_at: Optional[datetime] = None
    type: Literal['model']
