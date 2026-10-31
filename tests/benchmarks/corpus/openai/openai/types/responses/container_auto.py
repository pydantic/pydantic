# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .inline_skill import InlineSkill
from .skill_reference import SkillReference
from .container_network_policy_disabled import ContainerNetworkPolicyDisabled
from .container_network_policy_allowlist import ContainerNetworkPolicyAllowlist
NetworkPolicy: TypeAlias = Annotated[Union[ContainerNetworkPolicyDisabled, ContainerNetworkPolicyAllowlist], PropertyInfo(discriminator='type')]
Skill: TypeAlias = Annotated[Union[SkillReference, InlineSkill], PropertyInfo(discriminator='type')]

class ContainerAuto(BaseModel):
    type: Literal['container_auto']
    file_ids: Optional[List[str]] = None
    memory_limit: Optional[Literal['1g', '4g', '16g', '64g']] = None
    network_policy: Optional[NetworkPolicy] = None
    skills: Optional[List[Skill]] = None
