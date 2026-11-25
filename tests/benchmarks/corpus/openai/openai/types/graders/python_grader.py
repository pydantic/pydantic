# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class PythonGrader(BaseModel):
    """A PythonGrader object that runs a python script on the input."""
    name: str
    source: str
    type: Literal['python']
    image_tag: Optional[str] = None
