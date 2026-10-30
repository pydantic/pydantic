
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from ..beta_monetary_amount import BetaMonetaryAmount

class BetaManagedAgentsBudgetLimit(BaseModel):
    """A hard spend ceiling.

    The session stops issuing new model requests once the tracked list cost reaches `max_list_cost`.
    """
    max_list_cost: BetaMonetaryAmount
    type: Literal['limit']
