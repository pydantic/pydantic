
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaAnalyticsFederatedActorAWSProvider(BaseModel):
    account_id: str
    signed_principal: str
    type: Literal['aws']
