# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class MisalignmentSteer(BaseModel):
    """An optional public continuation instruction."""
    message: str

class Misalignment(BaseModel):
    detailed_explanation: Optional[str] = None
    error_type: Union[str, Literal['potentially_unintended_data_transfer', 'potentially_unintended_data_access', 'potentially_unintended_destructive_activity', 'other'], None] = None
    review_target: Optional[str] = None
    steer: Optional[MisalignmentSteer] = None

class ErrorObject(BaseModel):
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    type: str
    misalignment: Optional[Misalignment] = None
