# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class MultiAgentConfig(BaseModel):
    """The resolved configuration for creating and coordinating subagents."""
    enabled: bool
    max_concurrent_subagents: Optional[int] = None
