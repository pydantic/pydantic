# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class StringCheckGrader(BaseModel):
    """
    A StringCheckGrader object that performs a string comparison between input and reference using a specified operation.
    """
    input: str
    name: str
    operation: Literal['eq', 'ne', 'like', 'ilike']
    reference: str
    type: Literal['string_check']
