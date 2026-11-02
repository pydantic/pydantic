
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaThinkingMismatchAllowedInputTransformation(BaseModel):
    path: str
    reason: Literal['model_binding_mismatch', 'prefix_binding_mismatch', 'organization_binding_mismatch', 'end_user_binding_mismatch']
    type: Literal['thinking_mismatch_allowed']
