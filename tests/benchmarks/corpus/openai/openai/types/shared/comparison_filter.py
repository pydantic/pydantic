# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal
from ..._models import BaseModel

class ComparisonFilter(BaseModel):
    """
    A filter used to compare a specified attribute key to a given value using a defined comparison operation.
    """
    key: str
    type: Literal['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin']
    value: Union[str, float, bool, List[Union[str, float]]]
