
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_spend_limit_period import BetaSpendLimitPeriod
from .beta_spend_limit_user_actor import BetaSpendLimitUserActor
from .beta_spend_limit_user_scope import BetaSpendLimitUserScope
from .beta_spend_limit_seat_tier_scope import BetaSpendLimitSeatTierScope
from .beta_spend_limit_workspace_scope import BetaSpendLimitWorkspaceScope
from .beta_spend_limit_rbac_group_scope import BetaSpendLimitRBACGroupScope
from .beta_spend_limit_usage_tier_scope import BetaSpendLimitUsageTierScope
from .beta_spend_limit_organization_scope import BetaSpendLimitOrganizationScope
from .beta_spend_limit_scoped_api_key_actor import BetaSpendLimitScopedAPIKeyActor
from .beta_spend_limit_organization_service_scope import BetaSpendLimitOrganizationServiceScope
Actor: TypeAlias = Annotated[Union[BetaSpendLimitUserActor, BetaSpendLimitScopedAPIKeyActor], UnionDiscriminator('type')]
Scope: TypeAlias = Annotated[Union[BetaSpendLimitUserScope, BetaSpendLimitSeatTierScope, BetaSpendLimitRBACGroupScope, BetaSpendLimitOrganizationServiceScope, BetaSpendLimitOrganizationScope, BetaSpendLimitWorkspaceScope, BetaSpendLimitUsageTierScope], UnionDiscriminator('type')]
Source: TypeAlias = Annotated[Union[BetaSpendLimitUserScope, BetaSpendLimitSeatTierScope, BetaSpendLimitRBACGroupScope, BetaSpendLimitOrganizationServiceScope, BetaSpendLimitOrganizationScope, BetaSpendLimitWorkspaceScope, BetaSpendLimitUsageTierScope], UnionDiscriminator('type')]

class BetaSpendSummary(BaseModel):
    """Per-member effective-limit report row (`GET /spend_limits/effective`)."""
    actor: Actor
    amount: Optional[str] = None
    currency: str
    period: BetaSpendLimitPeriod
    period_to_date_spend: str
    scope: Scope
    source: Source
    spend_limit_id: str
