# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class MessageCreation(BaseModel):
    message_id: Optional[str] = None

class RunStepDeltaMessageDelta(BaseModel):
    """Details of the message creation by the run step."""
    type: Literal['message_creation']
    message_creation: Optional[MessageCreation] = None
