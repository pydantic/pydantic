
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaPackages(BaseModel):
    """Packages (and their versions) available in this environment."""
    apt: List[str]
    cargo: List[str]
    gem: List[str]
    go: List[str]
    npm: List[str]
    pip: List[str]
    type: Optional[Literal['packages']] = None
