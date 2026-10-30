
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._models import UnionDiscriminator
from .direct_caller import DirectCaller
from .server_tool_caller import ServerToolCaller
from .server_tool_caller_20260120 import ServerToolCaller20260120
ToolUseCaller: TypeAlias = Annotated[Union[DirectCaller, ServerToolCaller, ServerToolCaller20260120], UnionDiscriminator('type')]
