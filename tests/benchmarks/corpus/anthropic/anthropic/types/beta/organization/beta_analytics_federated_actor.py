
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_analytics_federated_actor_provider import BetaAnalyticsFederatedActorProvider

class BetaAnalyticsFederatedActor(BaseModel):
    provider: BetaAnalyticsFederatedActorProvider
    subject: Optional[str] = None
    type: Literal['federated_actor']
