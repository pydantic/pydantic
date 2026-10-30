# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_inline_skill import BetaInlineSkill
from .beta_skill_reference import BetaSkillReference
from .beta_container_network_policy_disabled import BetaContainerNetworkPolicyDisabled
from .beta_container_network_policy_allowlist import BetaContainerNetworkPolicyAllowlist
NetworkPolicy: TypeAlias = Annotated[Union[BetaContainerNetworkPolicyDisabled, BetaContainerNetworkPolicyAllowlist], PropertyInfo(discriminator='type')]
Skill: TypeAlias = Annotated[Union[BetaSkillReference, BetaInlineSkill], PropertyInfo(discriminator='type')]

class BetaContainerAuto(BaseModel):
    type: Literal['container_auto']
    file_ids: Optional[List[str]] = None
    memory_limit: Optional[Literal['1g', '4g', '16g', '64g']] = None
    network_policy: Optional[NetworkPolicy] = None
    skills: Optional[List[Skill]] = None
