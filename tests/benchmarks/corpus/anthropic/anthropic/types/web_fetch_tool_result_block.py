
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .direct_caller import DirectCaller
from .web_fetch_block import WebFetchBlock
from .server_tool_caller import ServerToolCaller
from .server_tool_caller_20260120 import ServerToolCaller20260120
from .web_fetch_tool_result_error_block import WebFetchToolResultErrorBlock
Caller: TypeAlias = Annotated[Union[DirectCaller, ServerToolCaller, ServerToolCaller20260120], UnionDiscriminator('type')]
Content: TypeAlias = Union[WebFetchToolResultErrorBlock, WebFetchBlock]

class WebFetchToolResultBlock(BaseModel):
    caller: Optional[Caller] = None
    content: Content
    tool_use_id: str
    type: Literal['web_fetch_tool_result']
