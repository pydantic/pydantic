# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class MessageCreation(BaseModel):
    message_id: str

class MessageCreationStepDetails(BaseModel):
    """Details of the message creation by the run step."""
    message_creation: MessageCreation
    type: Literal['message_creation']
