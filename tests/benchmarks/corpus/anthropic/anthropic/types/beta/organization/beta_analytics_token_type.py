
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaAnalyticsTokenType: TypeAlias = Literal['cache_creation.ephemeral_1h_input_tokens', 'cache_creation.ephemeral_5m_input_tokens', 'cache_read_input_tokens', 'output_tokens', 'uncached_input_tokens']
