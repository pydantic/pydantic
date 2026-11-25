
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaFallbackCreditNotApplied(BaseModel):
    """No reprice was applied; ``reason`` says why."""
    reason: Literal['body_mismatch', 'continuation_excluded', 'continuation_only', 'expired', 'invalid_target_model', 'not_enabled', 'reprice_unavailable', 'temporarily_unavailable', 'variant_fields_present', 'wrong_organization', 'wrong_platform', 'wrong_workspace']
    type: Literal['not_applied']
    remove_to_redeem: Optional[List[str]] = None
