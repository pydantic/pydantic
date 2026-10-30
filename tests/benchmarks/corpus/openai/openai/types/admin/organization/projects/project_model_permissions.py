# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from ....._models import BaseModel

class ProjectModelPermissions(BaseModel):
    """Represents the model allowlist or denylist policy for a project."""
    mode: Literal['allow_list', 'deny_list']
    api_model_ids: List[str] = FieldInfo(alias='model_ids')
    object: Literal['project.model_permissions']
