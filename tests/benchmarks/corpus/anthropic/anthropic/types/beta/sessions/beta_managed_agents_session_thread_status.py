
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
BetaManagedAgentsSessionThreadStatus: TypeAlias = Literal['running', 'idle', 'rescheduling', 'terminated']
