# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from ......_models import BaseModel

class AssignmentSource(BaseModel):
    principal_id: str
    principal_type: str

class RoleRetrieveResponse(BaseModel):
    """
    Detailed information about a role assignment entry returned when listing assignments.
    """
    id: str
    assignment_sources: Optional[List[AssignmentSource]] = None
    created_at: Optional[int] = None
    created_by: Optional[str] = None
    created_by_user_obj: Optional[Dict[str, object]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, object]] = None
    name: str
    permissions: List[str]
    predefined_role: bool
    resource_type: str
    updated_at: Optional[int] = None
