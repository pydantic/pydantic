
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_direct_caller import BetaDirectCaller
from .beta_server_tool_caller import BetaServerToolCaller
from .beta_server_tool_caller_20260120 import BetaServerToolCaller20260120
from .beta_web_search_tool_result_block_content import BetaWebSearchToolResultBlockContent
Caller: TypeAlias = Annotated[Union[BetaDirectCaller, BetaServerToolCaller, BetaServerToolCaller20260120], UnionDiscriminator('type')]

class BetaWebSearchToolResultBlock(BaseModel):
    content: BetaWebSearchToolResultBlockContent
    tool_use_id: str
    type: Literal['web_search_tool_result']
    caller: Optional[Caller] = None
