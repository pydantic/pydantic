
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_managed_agents_file_resource import BetaManagedAgentsFileResource
from .beta_managed_agents_memory_store_resource import BetaManagedAgentsMemoryStoreResource
from .beta_managed_agents_github_repository_resource import BetaManagedAgentsGitHubRepositoryResource
BetaManagedAgentsSessionResource: TypeAlias = Annotated[Union[BetaManagedAgentsGitHubRepositoryResource, BetaManagedAgentsFileResource, BetaManagedAgentsMemoryStoreResource], UnionDiscriminator('type')]
