# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel
from .decision_question import DecisionQuestion

class DecisionsDelegationUpdateConfig(BaseModel):
    model: Optional[str] = None
    questions: Optional[List[DecisionQuestion]] = None
