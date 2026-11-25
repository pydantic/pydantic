
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSkillVersion(BaseModel):
    id: str
    created_at: datetime
    description: str
    name: str
    skill_id: str
    type: Literal['skill_version']
