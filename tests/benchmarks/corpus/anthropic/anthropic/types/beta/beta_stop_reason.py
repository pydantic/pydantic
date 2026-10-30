
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaStopReason: TypeAlias = Literal['end_turn', 'max_tokens', 'stop_sequence', 'tool_use', 'pause_turn', 'compaction', 'refusal', 'model_context_window_exceeded']
