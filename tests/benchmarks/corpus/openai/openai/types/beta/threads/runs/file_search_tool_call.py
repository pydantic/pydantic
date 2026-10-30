# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ....._models import BaseModel

class FileSearchRankingOptions(BaseModel):
    """The ranking options for the file search."""
    ranker: Literal['auto', 'default_2024_08_21']
    score_threshold: float

class FileSearchResultContent(BaseModel):
    text: Optional[str] = None
    type: Optional[Literal['text']] = None

class FileSearchResult(BaseModel):
    """A result instance of the file search."""
    file_id: str
    file_name: str
    score: float
    content: Optional[List[FileSearchResultContent]] = None

class FileSearch(BaseModel):
    """For now, this is always going to be an empty object."""
    ranking_options: Optional[FileSearchRankingOptions] = None
    results: Optional[List[FileSearchResult]] = None

class FileSearchToolCall(BaseModel):
    id: str
    file_search: FileSearch
    type: Literal['file_search']
