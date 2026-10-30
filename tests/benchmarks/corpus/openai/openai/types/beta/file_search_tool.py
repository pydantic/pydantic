# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class FileSearchRankingOptions(BaseModel):
    """The ranking options for the file search.

    If not specified, the file search tool will use the `auto` ranker and a score_threshold of 0.

    See the [file search tool documentation](https://developers.openai.com/api/docs/guides/tools-file-search#retrieval-customization) for more information.
    """
    score_threshold: float
    ranker: Optional[Literal['auto', 'default_2024_08_21']] = None

class FileSearch(BaseModel):
    """Overrides for the file search tool."""
    max_num_results: Optional[int] = None
    ranking_options: Optional[FileSearchRankingOptions] = None

class FileSearchTool(BaseModel):
    type: Literal['file_search']
    file_search: Optional[FileSearch] = None
