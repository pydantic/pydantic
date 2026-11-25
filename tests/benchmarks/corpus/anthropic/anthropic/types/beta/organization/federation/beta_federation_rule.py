
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal
from ....._models import BaseModel
from .beta_federation_rule_match import BetaFederationRuleMatch
from .beta_service_account_target import BetaServiceAccountTarget

class BetaFederationRule(BaseModel):
    """Authorization rule binding an external OIDC identity to Anthropic.

    Evaluates the match conditions and mints an OAuth access token for the
    resolved target, scoped to a single workspace where the rule is enabled
    (chosen by the caller at exchange time when the rule is enabled for more
    than one). For rules enabled via `workspace_ids` or
    `applies_to_all_workspaces`, the target service account must be a member
    of that workspace (it is implicitly a member of the default workspace);
    rules carrying only the legacy `workspace_id` binding do not enforce
    this.
    """
    id: str
    applies_to_all_workspaces: bool
    archived_at: Optional[datetime] = None
    archived_by_actor_id: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    created_at: datetime
    created_by_actor_id: Optional[str] = None
    description: Optional[str] = None
    issuer_id: str
    issuer_name: Optional[str] = None
    match: BetaFederationRuleMatch
    name: str
    oauth_scope: str
    target: BetaServiceAccountTarget
    token_lifetime_seconds: int
    type: Literal['federation_rule']
    updated_at: datetime
    updated_by_actor_id: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_ids: List[str]
