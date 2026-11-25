
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_skill_source import BetaSkillSource

class BetaSkill(BaseModel):
    id: str
    created_at: datetime
    display_name: str
    latest_version_id: str
    source: BetaSkillSource
    type: Literal['skill']
    updated_at: datetime
