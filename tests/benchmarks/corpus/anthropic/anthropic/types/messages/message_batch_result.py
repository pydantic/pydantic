
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .message_batch_errored_result import MessageBatchErroredResult
from .message_batch_expired_result import MessageBatchExpiredResult
from .message_batch_canceled_result import MessageBatchCanceledResult
from .message_batch_succeeded_result import MessageBatchSucceededResult
MessageBatchResult: TypeAlias = Annotated[Union[MessageBatchSucceededResult, MessageBatchErroredResult, MessageBatchCanceledResult, MessageBatchExpiredResult], UnionDiscriminator('type')]
