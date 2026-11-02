
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .direct_caller import DirectCaller
from .server_tool_caller import ServerToolCaller
from .server_tool_caller_20260120 import ServerToolCaller20260120
Caller: TypeAlias = Annotated[Union[DirectCaller, ServerToolCaller, ServerToolCaller20260120], UnionDiscriminator('type')]

class ServerToolUseBlock(BaseModel):
    id: str
    caller: Optional[Caller] = None
    input: Dict[str, object]
    name: Literal['web_search', 'web_fetch', 'code_execution', 'bash_code_execution', 'text_editor_code_execution', 'tool_search_tool_regex', 'tool_search_tool_bm25']
    type: Literal['server_tool_use']
