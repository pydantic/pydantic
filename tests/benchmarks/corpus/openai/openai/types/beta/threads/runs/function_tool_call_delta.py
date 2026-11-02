# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class Function(BaseModel):
    """The definition of the function that was called."""
    arguments: Optional[str] = None
    name: Optional[str] = None
    output: Optional[str] = None

class FunctionToolCallDelta(BaseModel):
    index: int
    type: Literal['function']
    id: Optional[str] = None
    function: Optional[Function] = None
