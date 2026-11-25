
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .direct_caller import DirectCaller
from .server_tool_caller import ServerToolCaller
from .server_tool_caller_20260120 import ServerToolCaller20260120
from .web_search_tool_result_block_content import WebSearchToolResultBlockContent
Caller: TypeAlias = Annotated[Union[DirectCaller, ServerToolCaller, ServerToolCaller20260120], UnionDiscriminator('type')]

class WebSearchToolResultBlock(BaseModel):
    caller: Optional[Caller] = None
    content: WebSearchToolResultBlockContent
    tool_use_id: str
    type: Literal['web_search_tool_result']
