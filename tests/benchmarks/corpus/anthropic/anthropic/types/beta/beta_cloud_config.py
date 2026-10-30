
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_packages import BetaPackages
from .beta_limited_network import BetaLimitedNetwork
from .beta_unrestricted_network import BetaUnrestrictedNetwork
Networking: TypeAlias = Annotated[Union[BetaUnrestrictedNetwork, BetaLimitedNetwork], UnionDiscriminator('type')]

class BetaCloudConfig(BaseModel):
    """`cloud` environment configuration."""
    networking: Networking
    packages: BetaPackages
    type: Literal['cloud']
