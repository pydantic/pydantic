
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class UserProfileEfsFeature(BaseModel):
    """One feature of Enterprise Frontier Safeguards."""
    status: Literal['active', 'inactive']
