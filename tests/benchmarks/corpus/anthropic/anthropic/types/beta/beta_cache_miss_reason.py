
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_cache_miss_unavailable import BetaCacheMissUnavailable
from .beta_cache_miss_model_changed import BetaCacheMissModelChanged
from .beta_cache_miss_tools_changed import BetaCacheMissToolsChanged
from .beta_cache_miss_system_changed import BetaCacheMissSystemChanged
from .beta_cache_miss_messages_changed import BetaCacheMissMessagesChanged
from .beta_cache_miss_previous_message_not_found import BetaCacheMissPreviousMessageNotFound
BetaCacheMissReason: TypeAlias = Annotated[Union[BetaCacheMissModelChanged, BetaCacheMissSystemChanged, BetaCacheMissToolsChanged, BetaCacheMissMessagesChanged, BetaCacheMissPreviousMessageNotFound, BetaCacheMissUnavailable], UnionDiscriminator('type')]
