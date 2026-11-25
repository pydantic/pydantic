
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import TypeAlias
from .beta_web_search_result_block import BetaWebSearchResultBlock
from .beta_web_search_tool_result_error import BetaWebSearchToolResultError
BetaWebSearchToolResultBlockContent: TypeAlias = Union[BetaWebSearchToolResultError, List[BetaWebSearchResultBlock]]
