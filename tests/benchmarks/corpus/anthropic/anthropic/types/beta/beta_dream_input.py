
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_dream_sessions_input import BetaDreamSessionsInput
from .beta_dream_memory_store_input import BetaDreamMemoryStoreInput
BetaDreamInput: TypeAlias = Annotated[Union[BetaDreamMemoryStoreInput, BetaDreamSessionsInput], UnionDiscriminator('type')]
