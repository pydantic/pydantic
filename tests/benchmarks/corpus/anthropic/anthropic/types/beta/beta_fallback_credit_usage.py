
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_fallback_credit_redeemed import BetaFallbackCreditRedeemed
from .beta_fallback_credit_not_applied import BetaFallbackCreditNotApplied
Status: TypeAlias = Annotated[Union[BetaFallbackCreditRedeemed, BetaFallbackCreditNotApplied], UnionDiscriminator('type')]

class BetaFallbackCreditUsage(BaseModel):
    """Outcome of the ``fallback_credit_token`` presented on this request."""
    status: Status
