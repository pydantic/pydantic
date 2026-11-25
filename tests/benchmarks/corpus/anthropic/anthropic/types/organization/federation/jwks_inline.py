
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List
from typing_extensions import Literal
from ...._models import BaseModel

class JWKSInline(BaseModel):
    """JWKS supplied directly; no network fetch."""
    keys: List[Dict[str, object]]
    type: Literal['inline']
