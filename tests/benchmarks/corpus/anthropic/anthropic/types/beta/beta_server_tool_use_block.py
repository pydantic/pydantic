
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_direct_caller import BetaDirectCaller
from .beta_server_tool_caller import BetaServerToolCaller
from .beta_server_tool_caller_20260120 import BetaServerToolCaller20260120
Caller: TypeAlias = Annotated[Union[BetaDirectCaller, BetaServerToolCaller, BetaServerToolCaller20260120], UnionDiscriminator('type')]

class BetaServerToolUseBlock(BaseModel):
    id: str
    input: Dict[str, object]
    name: Literal['advisor', 'web_search', 'web_fetch', 'code_execution', 'bash_code_execution', 'text_editor_code_execution', 'tool_search_tool_regex', 'tool_search_tool_bm25']
    type: Literal['server_tool_use']
    caller: Optional[Caller] = None
