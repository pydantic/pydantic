# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class UserDeleteResponse(BaseModel):
    """Confirmation payload returned after removing a user from a group."""
    deleted: bool
    object: Literal['group.user.deleted']
