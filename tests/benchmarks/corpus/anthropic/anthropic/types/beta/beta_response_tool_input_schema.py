
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaResponseToolInputSchema(BaseModel):
    """[JSON schema](https://json-schema.org/draft/2020-12) for this tool's input.

    This defines the shape of the `input` that your tool accepts and that the model will produce.
    """
    type: Literal['object']
    properties: Optional[Dict[str, object]] = None
    required: Optional[List[str]] = None
    __pydantic_extra__: Dict[str, object]
