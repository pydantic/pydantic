# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .response import Response
from ..._models import BaseModel

class ResponseIncompleteEvent(BaseModel):
    """An event that is emitted when a response finishes as incomplete.

    Over WebSocket, steering can finish a response with
    `response.incomplete_details.reason` set to `steered`, followed automatically
    by a successor `response.created` that commits the queued steering input.
    """
    response: Response
    sequence_number: int
    type: Literal['response.incomplete']
