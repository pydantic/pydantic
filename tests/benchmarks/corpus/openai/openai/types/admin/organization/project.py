# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .project_residency import ProjectResidency

class Project(BaseModel):
    """Represents an individual project."""
    id: str
    created_at: int
    object: Literal['organization.project']
    archived_at: Optional[int] = None
    external_key_id: Optional[str] = None
    name: Optional[str] = None
    residency: Optional[ProjectResidency] = None
    status: Optional[str] = None
