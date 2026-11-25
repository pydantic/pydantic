
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .workspace_rate_limit_workspace_source import WorkspaceRateLimitWorkspaceSource
from .workspace_rate_limit_organization_source import WorkspaceRateLimitOrganizationSource
Source: TypeAlias = Annotated[Union[WorkspaceRateLimitWorkspaceSource, WorkspaceRateLimitOrganizationSource], UnionDiscriminator('type')]

class WorkspaceRateLimitValue(BaseModel):
    org_limit: Optional[int] = None
    source: Source
    type: str
    value: int
