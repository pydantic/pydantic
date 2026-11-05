# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List
from typing_extensions import Literal
from ..._models import BaseModel

class ToolChoiceAllowed(BaseModel):
    """Constrains the tools available to the model to a pre-defined set."""
    mode: Literal['auto', 'required']
    tools: List[Dict[str, object]]
    type: Literal['allowed_tools']
