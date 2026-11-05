# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ToolSearchTool(BaseModel):
    """Hosted or BYOT tool search configuration for deferred tools."""
    type: Literal['tool_search']
    description: Optional[str] = None
    execution: Optional[Literal['server', 'client']] = None
    parameters: Optional[object] = None
