# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseErrorEvent(BaseModel):
    """Emitted when an error occurs."""
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    sequence_number: int
    type: Literal['error']
