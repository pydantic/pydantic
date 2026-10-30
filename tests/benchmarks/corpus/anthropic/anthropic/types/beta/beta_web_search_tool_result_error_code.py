
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaWebSearchToolResultErrorCode: TypeAlias = Literal['invalid_tool_input', 'unavailable', 'max_uses_exceeded', 'too_many_requests', 'query_too_long', 'request_too_large']
