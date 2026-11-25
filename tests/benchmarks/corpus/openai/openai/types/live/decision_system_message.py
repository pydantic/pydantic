# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .decision_input_text import DecisionInputText

class DecisionSystemMessage(BaseModel):
    content: Union[str, List[DecisionInputText]]
    role: Literal['system']
    id: Optional[str] = None
    type: Optional[Literal['message']] = None
