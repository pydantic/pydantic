
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from ..beta_managed_agents_branch_checkout import BetaManagedAgentsBranchCheckout
from ..beta_managed_agents_commit_checkout import BetaManagedAgentsCommitCheckout
Checkout: TypeAlias = Annotated[Union[BetaManagedAgentsBranchCheckout, BetaManagedAgentsCommitCheckout, None], UnionDiscriminator('type')]

class BetaManagedAgentsGitHubRepositoryResource(BaseModel):
    id: str
    created_at: datetime
    mount_path: str
    type: Literal['github_repository']
    updated_at: datetime
    url: str
    checkout: Optional[Checkout] = None
