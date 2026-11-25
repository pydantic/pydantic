# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class UserCreateResponse(BaseModel):
    """Confirmation payload returned after adding a user to a group."""
    group_id: str
    object: Literal['group.user']
    user_id: str
