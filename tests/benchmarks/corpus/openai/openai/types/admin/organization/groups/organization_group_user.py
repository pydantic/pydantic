# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ....._models import BaseModel

class OrganizationGroupUser(BaseModel):
    """Represents an individual user returned when inspecting group membership."""
    id: str
    email: Optional[str] = None
    name: str
