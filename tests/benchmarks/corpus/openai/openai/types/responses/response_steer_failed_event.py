# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .response_steer_input import ResponseSteerInput
from .response_steer_error_code import ResponseSteerErrorCode

class Error(BaseModel):
    """Information about why the input could not be committed."""
    code: ResponseSteerErrorCode
    message: str
    type: Literal['invalid_request_error']

class Steer(BaseModel):
    """The steering submission that could not be committed."""
    input: ResponseSteerInput
    previous_response_id: str
    id: Optional[str] = None

class ResponseSteerFailedEvent(BaseModel):
    """
    Emitted when steering input is rejected or cannot be committed to a
    successor response. Returns the original, uncommitted input so the client
    can carry it into `response.create` when appropriate. Invalid input must
    be corrected before retrying.

    Failures after acceptance include the same steering ID. Failures before an
    ID is allocated omit `steer.id`. A lost connection or missing acknowledgement
    leaves the outcome unknown; it is not proof that the input was rejected.
    """
    error: Error
    sequence_number: int
    steer: Steer
    type: Literal['response.steer.failed']
    stream_id: Optional[str] = None
