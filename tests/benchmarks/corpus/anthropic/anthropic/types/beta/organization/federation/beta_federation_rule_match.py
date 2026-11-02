
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from ....._models import BaseModel

class BetaFederationRuleMatch(BaseModel):
    """Does the incoming JWT qualify?

    All populated fields must pass; omitted fields are skipped. At least one
    of `subject_prefix` (other than a wildcard-only value like `*`), `claims`,
    or `condition` is required; `audience` alone is not sufficient.
    """
    audience: Optional[str] = None
    claims: Optional[Dict[str, str]] = None
    condition: Optional[str] = None
    subject_prefix: Optional[str] = None
