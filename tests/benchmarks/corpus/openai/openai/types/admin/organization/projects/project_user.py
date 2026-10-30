# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class ProjectUser(BaseModel):
    """Represents an individual user in a project."""
    id: str
    added_at: int
    object: Literal['organization.project.user']
    role: str
    email: Optional[str] = None
    name: Optional[str] = None
