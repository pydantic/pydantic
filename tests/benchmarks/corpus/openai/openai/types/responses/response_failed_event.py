# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .response import Response
from ..._models import BaseModel

class ResponseFailedEvent(BaseModel):
    """An event that is emitted when a response fails."""
    response: Response
    sequence_number: int
    type: Literal['response.failed']
