
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ServiceAccountTarget(BaseModel):
    """Bind to a fixed service account by ID."""
    service_account_id: str
    type: Literal['service_account']
    service_account_name: Optional[str] = None
