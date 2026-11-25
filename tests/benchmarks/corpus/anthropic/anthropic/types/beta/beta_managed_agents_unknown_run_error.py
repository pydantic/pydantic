
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsUnknownRunError(BaseModel):
    """An unknown or unexpected error caused the run to fail.

    A fallback variant; clients that do not recognize a new error type can match on message alone.
    """
    message: str
    type: Literal['unknown_error']
