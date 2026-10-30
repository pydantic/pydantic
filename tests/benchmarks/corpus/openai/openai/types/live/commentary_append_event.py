# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class CommentaryAppendEvent(BaseModel):
    """
    Provide context the Live model can communicate to the user, optionally for an existing client delegation. Rejected while an audio fixture is active.
    """
    content: str
    delegation_id: Optional[str] = None
    type: Literal['session.commentary.append']
    event_id: Optional[str] = None
