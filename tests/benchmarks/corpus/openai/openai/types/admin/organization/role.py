# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Role(BaseModel):
    """Details about a role that can be assigned through the public Roles API."""
    id: str
    description: Optional[str] = None
    name: str
    object: Literal['role']
    permissions: List[str]
    predefined_role: bool
    resource_type: str
