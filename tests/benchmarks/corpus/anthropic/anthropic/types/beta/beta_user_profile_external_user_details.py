
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ..._models import BaseModel

class BetaUserProfileExternalUserDetails(BaseModel):
    """Details about the entity this profile represents, as the platform states them.

    Anthropic does not verify them. Every field is present, `null` until the platform supplies a value.
    """
    account_status: Optional[Literal['active', 'suspended', 'blocked']] = None
    country: Optional[str] = None
    email_hash: Optional[str] = None
    entity_type: Optional[Literal['individual', 'business', 'non_profit', 'government']] = None
    name_hash: Optional[str] = None
    onboarded_at: Optional[datetime] = None
    reference_id: Optional[str] = None
