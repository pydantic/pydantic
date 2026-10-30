
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from .._models import BaseModel, UnionDiscriminator
from .direct_caller import DirectCaller
from .server_tool_caller import ServerToolCaller
from .server_tool_caller_20260120 import ServerToolCaller20260120
Caller: TypeAlias = Annotated[Union[DirectCaller, ServerToolCaller, ServerToolCaller20260120], UnionDiscriminator('type')]

class ToolUseBlock(BaseModel):
    id: str
    caller: Optional[Caller] = None
    input: Dict[str, object]
    name: str
    type: Literal['tool_use']
    toolset_name: Optional[str] = None
