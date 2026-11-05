# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class ProjectGroup(BaseModel):
    """Details about a group's membership in a project."""
    created_at: int
    group_id: str
    group_name: str
    group_type: Literal['group', 'tenant_group']
    object: Literal['project.group']
    project_id: str
