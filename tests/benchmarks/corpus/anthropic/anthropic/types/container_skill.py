
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class ContainerSkill(BaseModel):
    """A skill that was loaded in a container (response model)."""
    skill_id: str
    type: Literal['anthropic', 'custom']
    version: str
