# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from pydantic import StrictStr, StrictBool
from ..._models import BaseModel

class DecisionChoiceOption(BaseModel):
    value: Union[StrictStr, StrictBool]
    description: Optional[str] = None
