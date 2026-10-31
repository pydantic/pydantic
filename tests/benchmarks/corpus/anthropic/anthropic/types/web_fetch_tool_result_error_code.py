
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
WebFetchToolResultErrorCode: TypeAlias = Literal['invalid_tool_input', 'url_too_long', 'url_not_allowed', 'url_not_in_prior_context', 'url_not_accessible', 'unsupported_content_type', 'too_many_requests', 'max_uses_exceeded', 'unavailable', 'content_too_large']
