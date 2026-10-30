
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsUnknownDeploymentPausedReasonError(BaseModel):
    """An unrecognized error auto-paused the deployment.

    A fallback variant; matches a run whose `error.type` is `unknown_error`.
    """
    type: Literal['unknown_error']
