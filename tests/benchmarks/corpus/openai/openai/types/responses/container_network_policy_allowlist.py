# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .container_network_policy_domain_secret import ContainerNetworkPolicyDomainSecret

class ContainerNetworkPolicyAllowlist(BaseModel):
    allowed_domains: List[str]
    type: Literal['allowlist']
    domain_secrets: Optional[List[ContainerNetworkPolicyDomainSecret]] = None
