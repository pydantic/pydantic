# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Vault(BaseModel):
    """A collection of credentials for MCP servers and OpenAI-hosted environments."""
    id: str
    created_at: int
    metadata: Dict[str, str]
    name: Optional[str] = None
    object: Literal['vault']
