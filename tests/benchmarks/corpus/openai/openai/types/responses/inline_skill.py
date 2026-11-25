# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .inline_skill_source import InlineSkillSource

class InlineSkill(BaseModel):
    description: str
    name: str
    source: InlineSkillSource
    type: Literal['inline']
