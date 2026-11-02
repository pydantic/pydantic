# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_local_skill import BetaLocalSkill

class BetaLocalEnvironment(BaseModel):
    type: Literal['local']
    skills: Optional[List[BetaLocalSkill]] = None
