# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class FunctionTool(BaseModel):
    """
    A function tool available to the Responses backend when the Live model delegates a task.
    """
    name: str
    type: Literal['function']
    description: Optional[str] = None
    parameters: Optional[Dict[str, object]] = None
    strict: Optional[bool] = None
