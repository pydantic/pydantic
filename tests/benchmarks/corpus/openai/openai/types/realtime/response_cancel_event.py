# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseCancelEvent(BaseModel):
    """Send this event to cancel an in-progress response.

    The server will respond
    with a `response.done` event with a status of `response.status=cancelled`. If
    there is no response to cancel, the server will respond with an error. It's safe
    to call `response.cancel` even if no response is in progress, an error will be
    returned the session will remain unaffected.
    """
    type: Literal['response.cancel']
    event_id: Optional[str] = None
    response_id: Optional[str] = None
