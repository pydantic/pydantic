
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_spend_limit_period import BetaSpendLimitPeriod
from .beta_spend_limit_user_scope import BetaSpendLimitUserScope
from .beta_spend_limit_seat_tier_scope import BetaSpendLimitSeatTierScope
from .beta_spend_limit_workspace_scope import BetaSpendLimitWorkspaceScope
from .beta_spend_limit_rbac_group_scope import BetaSpendLimitRBACGroupScope
from .beta_spend_limit_usage_tier_scope import BetaSpendLimitUsageTierScope
from .beta_spend_limit_organization_scope import BetaSpendLimitOrganizationScope
from .beta_spend_limit_organization_service_scope import BetaSpendLimitOrganizationServiceScope
Scope: TypeAlias = Annotated[Union[BetaSpendLimitUserScope, BetaSpendLimitSeatTierScope, BetaSpendLimitRBACGroupScope, BetaSpendLimitOrganizationServiceScope, BetaSpendLimitOrganizationScope, BetaSpendLimitWorkspaceScope, BetaSpendLimitUsageTierScope], UnionDiscriminator('type')]

class BetaSpendLimit(BaseModel):
    """A configured spend limit: a cap on metered spend for one scope and period."""
    id: str
    amount: Optional[str] = None
    created_at: datetime
    currency: str
    is_enabled: bool
    period: BetaSpendLimitPeriod
    scope: Scope
    type: Literal['spend_limit']
    updated_at: datetime
