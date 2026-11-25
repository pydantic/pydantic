# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ToolChoiceCustom(BaseModel):
    """Use this option to force the model to call a specific custom tool."""
    name: str
    type: Literal['custom']
