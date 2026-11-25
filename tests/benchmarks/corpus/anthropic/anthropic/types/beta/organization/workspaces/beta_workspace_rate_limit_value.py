
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from .beta_workspace_rate_limit_workspace_source import BetaWorkspaceRateLimitWorkspaceSource
from .beta_workspace_rate_limit_organization_source import BetaWorkspaceRateLimitOrganizationSource
Source: TypeAlias = Annotated[Union[BetaWorkspaceRateLimitWorkspaceSource, BetaWorkspaceRateLimitOrganizationSource], UnionDiscriminator('type')]

class BetaWorkspaceRateLimitValue(BaseModel):
    org_limit: Optional[int] = None
    source: Source
    type: str
    value: int
