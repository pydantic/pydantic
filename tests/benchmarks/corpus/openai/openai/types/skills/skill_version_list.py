# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .skill_version import SkillVersion

class SkillVersionList(BaseModel):
    data: List[SkillVersion]
    first_id: Optional[str] = None
    has_more: bool
    last_id: Optional[str] = None
    object: Literal['list']
