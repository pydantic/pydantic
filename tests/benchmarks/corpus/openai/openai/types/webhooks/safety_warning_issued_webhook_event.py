# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    id: str

class SafetyWarningIssuedWebhookEvent(BaseModel):
    """Sent when a warning is issued for a safety identifier in your organization."""
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['safety.warning_issued']
