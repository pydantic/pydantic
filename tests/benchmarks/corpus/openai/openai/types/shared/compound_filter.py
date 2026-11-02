# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from .comparison_filter import ComparisonFilter
Filter: TypeAlias = Union[ComparisonFilter, object]

class CompoundFilter(BaseModel):
    """Combine multiple filters using `and` or `or`."""
    filters: List[Filter]
    type: Literal['and', 'or']
