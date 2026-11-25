# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class NotificationChannel(BaseModel):
    """Email notification settings for a spend alert."""
    recipients: List[str]
    type: Literal['email']
    subject_prefix: Optional[str] = None

class OrganizationSpendAlert(BaseModel):
    """Represents a spend alert configured at the organization level."""
    id: str
    currency: Literal['USD']
    interval: Literal['month']
    notification_channel: NotificationChannel
    object: Literal['organization.spend_alert']
    threshold_amount: int
