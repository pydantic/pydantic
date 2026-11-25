
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_direct_caller import BetaDirectCaller
from .beta_server_tool_caller import BetaServerToolCaller
from .beta_server_tool_caller_20260120 import BetaServerToolCaller20260120
BetaToolUseCaller: TypeAlias = Annotated[Union[BetaDirectCaller, BetaServerToolCaller, BetaServerToolCaller20260120], UnionDiscriminator('type')]
