
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_branch_checkout import BetaManagedAgentsBranchCheckout
from .beta_managed_agents_commit_checkout import BetaManagedAgentsCommitCheckout
Checkout: TypeAlias = Annotated[Union[BetaManagedAgentsBranchCheckout, BetaManagedAgentsCommitCheckout, None], UnionDiscriminator('type')]

class BetaManagedAgentsGitHubRepositoryResourceConfig(BaseModel):
    """A GitHub repository mounted into each session's container.

    The authorization token is write-only and never returned.
    """
    type: Literal['github_repository']
    url: str
    checkout: Optional[Checkout] = None
    mount_path: Optional[str] = None
