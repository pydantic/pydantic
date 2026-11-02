# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .hosted_skill_reference import HostedSkillReference

class HostedSkillResourceInline(BaseModel):
    """A skill installed from an inline ZIP archive."""
    description: str
    name: str
    type: Literal['inline']
HostedSkill: TypeAlias = Annotated[Union[HostedSkillReference, HostedSkillResourceInline], PropertyInfo(discriminator='type')]
