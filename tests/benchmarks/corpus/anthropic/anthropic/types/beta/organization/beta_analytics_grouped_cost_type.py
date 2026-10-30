
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaAnalyticsGroupedCostType: TypeAlias = Literal['code_execution', 'session_usage', 'tokens', 'web_search']
