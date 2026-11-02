
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from .._models import BaseModel
from .skill_source import SkillSource

class Skill(BaseModel):
    id: str
    created_at: datetime
    display_name: str
    latest_version_id: str
    source: SkillSource
    type: Literal['skill']
    updated_at: datetime
