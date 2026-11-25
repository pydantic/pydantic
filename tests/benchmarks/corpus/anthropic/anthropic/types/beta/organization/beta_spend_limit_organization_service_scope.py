
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaSpendLimitOrganizationServiceScope(BaseModel):
    service: str
    type: Literal['organization_service']
