# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class Error(BaseModel):
    """
    Details of an error encountered by the Live session, including the affected parameter or client command when available.
    """
    code: str
    message: str
    type: str
    client_event_id: Optional[str] = None
    param: Optional[str] = None
