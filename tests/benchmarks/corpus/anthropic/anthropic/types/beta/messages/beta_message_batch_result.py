
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_message_batch_errored_result import BetaMessageBatchErroredResult
from .beta_message_batch_expired_result import BetaMessageBatchExpiredResult
from .beta_message_batch_canceled_result import BetaMessageBatchCanceledResult
from .beta_message_batch_succeeded_result import BetaMessageBatchSucceededResult
BetaMessageBatchResult: TypeAlias = Annotated[Union[BetaMessageBatchSucceededResult, BetaMessageBatchErroredResult, BetaMessageBatchCanceledResult, BetaMessageBatchExpiredResult], UnionDiscriminator('type')]
