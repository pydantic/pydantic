# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class OutputText(BaseModel):
    """A text content part produced by the agent."""
    text: str
    type: Literal['output_text']
