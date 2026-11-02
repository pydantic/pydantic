
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel
from .beta_currency import BetaCurrency

class BetaMonetaryAmount(BaseModel):
    """A monetary amount in a specific currency."""
    amount: str
    currency: BetaCurrency
