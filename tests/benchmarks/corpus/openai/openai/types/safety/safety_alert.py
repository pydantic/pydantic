# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class SafetyAlert(BaseModel):
    id: str
    created_at: int
    error_type: Literal['potentially_unintended_data_transfer', 'potentially_unintended_data_access', 'potentially_unintended_destructive_activity', 'other']
    model: str
    object: Literal['safety.alert']
    reason: Optional[str] = None
    request_id: str
    request_paused: bool
    response_id: str
    detailed_explanation: Optional[str] = None
