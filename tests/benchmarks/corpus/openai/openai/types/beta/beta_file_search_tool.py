# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel

class FiltersComparisonFilter(BaseModel):
    """
    A filter used to compare a specified attribute key to a given value using a defined comparison operation.
    """
    key: str
    type: Literal['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin']
    value: Union[str, float, bool, List[Union[str, float]]]

class FiltersCompoundFilterFilterComparisonFilter(BaseModel):
    """
    A filter used to compare a specified attribute key to a given value using a defined comparison operation.
    """
    key: str
    type: Literal['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin']
    value: Union[str, float, bool, List[Union[str, float]]]
FiltersCompoundFilterFilter: TypeAlias = Union[FiltersCompoundFilterFilterComparisonFilter, object]

class FiltersCompoundFilter(BaseModel):
    """Combine multiple filters using `and` or `or`."""
    filters: List[FiltersCompoundFilterFilter]
    type: Literal['and', 'or']
Filters: TypeAlias = Union[FiltersComparisonFilter, FiltersCompoundFilter, None]

class RankingOptionsHybridSearch(BaseModel):
    """
    Weights that control how reciprocal rank fusion balances semantic embedding matches versus sparse keyword matches when hybrid search is enabled.
    """
    embedding_weight: float
    text_weight: float

class RankingOptions(BaseModel):
    """Ranking options for search."""
    hybrid_search: Optional[RankingOptionsHybridSearch] = None
    ranker: Optional[Literal['auto', 'default-2024-11-15']] = None
    score_threshold: Optional[float] = None

class BetaFileSearchTool(BaseModel):
    """A tool that searches for relevant content from uploaded files.

    Learn more about the [file search tool](https://developers.openai.com/api/docs/guides/tools-file-search).
    """
    type: Literal['file_search']
    vector_store_ids: List[str]
    filters: Optional[Filters] = None
    max_num_results: Optional[int] = None
    ranking_options: Optional[RankingOptions] = None
