# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class Data(BaseModel):
    id: str

class SafetyAlertCreatedWebhookEvent(BaseModel):
    """Sent when an approved safety alert is available for an API project."""
    id: str
    created_at: int
    data: Data
    object: Literal['event']
    type: Literal['safety.alert.created']
