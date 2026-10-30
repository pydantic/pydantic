# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaApplyPatchTool(BaseModel):
    """Allows the assistant to create, delete, or update files using unified diffs."""
    type: Literal['apply_patch']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
