# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class SessionCloseEvent(BaseModel):
    """Request that the Live session close.

    The terminal `session.closed` event contains the close reason and final usage.
    """
    type: Literal['session.close']
    event_id: Optional[str] = None
