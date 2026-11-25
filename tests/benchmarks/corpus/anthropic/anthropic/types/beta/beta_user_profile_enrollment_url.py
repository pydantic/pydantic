
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaUserProfileEnrollmentURL(BaseModel):
    """
    A URL to give to the entity that a user profile represents, so that the entity can enroll in a program.
    """
    expires_at: datetime
    type: Literal['enrollment_url']
    url: str
