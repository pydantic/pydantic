
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._models import UnionDiscriminator
from .cache_miss_unavailable import CacheMissUnavailable
from .cache_miss_model_changed import CacheMissModelChanged
from .cache_miss_tools_changed import CacheMissToolsChanged
from .cache_miss_system_changed import CacheMissSystemChanged
from .cache_miss_messages_changed import CacheMissMessagesChanged
from .cache_miss_previous_message_not_found import CacheMissPreviousMessageNotFound
CacheMissReason: TypeAlias = Annotated[Union[CacheMissModelChanged, CacheMissSystemChanged, CacheMissToolsChanged, CacheMissMessagesChanged, CacheMissPreviousMessageNotFound, CacheMissUnavailable], UnionDiscriminator('type')]
