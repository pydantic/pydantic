
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import TypeAlias
from .web_search_result_block import WebSearchResultBlock
from .web_search_tool_result_error import WebSearchToolResultError
WebSearchToolResultBlockContent: TypeAlias = Union[WebSearchToolResultError, List[WebSearchResultBlock]]
