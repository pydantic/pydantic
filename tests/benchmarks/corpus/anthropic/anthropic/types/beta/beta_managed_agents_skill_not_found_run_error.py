
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSkillNotFoundRunError(BaseModel):
    """A skill referenced by the deployment's agent no longer exists."""
    message: str
    type: Literal['skill_not_found_error']
