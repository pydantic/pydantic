# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_container_network_policy_domain_secret import BetaContainerNetworkPolicyDomainSecret

class BetaContainerNetworkPolicyAllowlist(BaseModel):
    allowed_domains: List[str]
    type: Literal['allowlist']
    domain_secrets: Optional[List[BetaContainerNetworkPolicyDomainSecret]] = None
