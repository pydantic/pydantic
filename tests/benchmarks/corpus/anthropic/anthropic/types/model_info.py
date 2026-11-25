
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel
from .model_line import ModelLine
from .model_capabilities import ModelCapabilities

class ModelInfo(BaseModel):
    id: str
    capabilities: Optional[ModelCapabilities] = None
    created_at: datetime
    deprecated_at: Optional[datetime] = None
    display_name: str
    lifecycle: Literal['active', 'deprecated', 'retired']
    line: Optional[ModelLine] = None
    max_input_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    retires_at: Optional[datetime] = None
    type: Literal['model']
