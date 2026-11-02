
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSkillNotFoundDeploymentPausedReasonError(BaseModel):
    """A skill referenced by the deployment's agent no longer exists."""
    type: Literal['skill_not_found_error']
