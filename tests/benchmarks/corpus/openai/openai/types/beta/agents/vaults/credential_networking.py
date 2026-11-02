# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel

class VaultCredentialNetworkingResourceUnrestricted(BaseModel):
    """Allows substitution for destinations permitted by the environment network policy.

    Requires `environment.network.access` to be `restricted`, with explicit `allowed_domains`.
    """
    type: Literal['unrestricted']

class VaultCredentialNetworkingResourceLimited(BaseModel):
    """Allows substitution only for the listed hosts.

    The environment network policy must also allow these hosts.
    """
    allowed_hosts: List[str]
    type: Literal['limited']
CredentialNetworking: TypeAlias = Annotated[Union[VaultCredentialNetworkingResourceUnrestricted, VaultCredentialNetworkingResourceLimited], PropertyInfo(discriminator='type')]
